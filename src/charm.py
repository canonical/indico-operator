#!/usr/bin/env python3

# Copyright 2022 Canonical Ltd.
# Licensed under the GPLv3, see LICENCE file for details.

"""Charm for Indico on kubernetes."""
import logging
import os
from urllib.parse import urlparse

import ops.lib
from charms.nginx_ingress_integrator.v0.ingress import IngressRequires
from charms.redis_k8s.v0.redis import RedisRelationCharmEvents, RedisRequires
from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, MaintenanceStatus, WaitingStatus
from ops.pebble import ExecError

DATABASE_NAME = "indico"
PORT = 8080
INDICO_CUSTOMIZATION_DIR = "/srv/indico/custom"

pgsql = ops.lib.use("pgsql", 1, "postgresql-charmers@lists.launchpad.net")


class IndicoOperatorCharm(CharmBase):
    """Charm for Indico on kubernetes."""

    _stored = StoredState()
    on = RedisRelationCharmEvents()

    def __init__(self, *args):
        super().__init__(*args)

        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.leader_elected, self._on_config_changed)
        self.framework.observe(self.on.indico_pebble_ready, self._on_pebble_ready)
        self.framework.observe(self.on.indico_celery_pebble_ready, self._on_pebble_ready)
        self.framework.observe(self.on.indico_nginx_pebble_ready, self._on_pebble_ready)
        self.framework.observe(
            self.on.refresh_customization_changes_action, self._refresh_customization_changes
        )

        self._stored.set_default(
            db_conn_str=None,
            db_uri=None,
            db_ro_uris=[],
            redis_relation={},
            # This key would need to be shared across instances to support horizontal scalability
            secret_key=repr(os.urandom(32)),
            pebble_statuses={
                "indico": False,
                "indico-nginx": False,
                "indico-celery": False,
            },
        )

        self.db = pgsql.PostgreSQLClient(self, "db")
        self.framework.observe(
            self.db.on.database_relation_joined, self._on_database_relation_joined
        )
        self.framework.observe(self.db.on.master_changed, self._on_master_changed)

        self.redis = RedisRequires(self, self._stored)
        self.framework.observe(self.on.redis_relation_updated, self._on_config_changed)

        self.ingress = IngressRequires(self, self._make_ingress_config())

    def _on_database_relation_joined(self, event: pgsql.DatabaseRelationJoinedEvent):
        """Handle db-relation-joined."""
        if self.model.unit.is_leader():
            # Provide requirements to the PostgreSQL server.
            event.database = DATABASE_NAME
            event.extensions = ["pg_trgm:public", "unaccent:public"]
        elif event.database != DATABASE_NAME:
            # Leader has not yet set requirements. Defer, in case this unit
            # becomes leader and needs to perform that operation.
            event.defer()
            return

    def _on_master_changed(self, event: pgsql.MasterChangedEvent):
        """Handle changes in the primary database unit."""
        if event.database != DATABASE_NAME:
            # Leader has not yet set requirements. Wait until next
            # event, or risk connecting to an incorrect database.
            return

        self._stored.db_conn_str = None if event.master is None else event.master.conn_str
        self._stored.db_uri = None if event.master is None else event.master.uri

        if event.master is None:
            return

        self._on_config_changed(event)

    def _make_ingress_config(self):
        """Return ingress configuration."""
        return {
            "service-hostname": self._get_external_hostname(),
            "service-name": self.app.name,
            "service-port": 8080,
        }

    def _are_pebble_instances_ready(self):
        """Check if all pebble instances are ready."""
        return all(self._stored.pebble_statuses.values())

    def _get_external_hostname(self):
        """Extract and return hostname from site_url."""
        site_url = self.config["site_url"]
        return urlparse(site_url).hostname if site_url else self.app.name

    def _get_external_scheme(self):
        """Extract and return schema from site_url."""
        site_url = self.config["site_url"]
        return urlparse(site_url).scheme if site_url else "http"

    def _get_external_port(self):
        """Extract and return port from site_url."""
        site_url = self.config["site_url"]
        return urlparse(site_url).port

    def _are_relations_ready(self):
        """Handle the on pebble ready event for Indico."""
        if not self._stored.redis_relation:
            self.unit.status = WaitingStatus("Waiting for redis relation")
            return False

        if not self._stored.db_uri:
            self.unit.status = WaitingStatus("Waiting for database relation")
            return False

        return True

    def _on_pebble_ready(self, event):
        """Handle the on pebble ready event for the containers."""
        if not self._are_relations_ready():
            event.defer()
            return
        self._config_pebble(event.workload)

    def _config_pebble(self, container):
        """Apply pebble changes."""
        pebble_config = self._get_pebble_config(container.name)
        self.unit.status = MaintenanceStatus("Adding {} layer to pebble".format(container.name))
        container.add_layer(container.name, pebble_config, combine=True)
        self.unit.status = MaintenanceStatus("Starting {} container".format(container.name))
        container.pebble.replan_services()
        self._stored.pebble_statuses[container.name] = True
        if self._are_pebble_instances_ready():
            self.unit.status = ActiveStatus()
        else:
            self.unit.status = WaitingStatus("Waiting for pebble")

    def _get_pebble_config(self, container_name):
        """Generate pebble config."""
        indico_env_config = self._get_indico_env_config()
        configuration = {
            "indico": {
                "summary": "Indico layer",
                "description": "Indico layer",
                "services": {
                    "indico": {
                        "override": "replace",
                        "summary": "Indico service",
                        "command": "/srv/indico/start-indico.sh",
                        "startup": "enabled",
                        "user": "indico",
                        "environment": indico_env_config,
                    },
                },
            },
            "indico-celery": {
                "summary": "Indico celery layer",
                "description": "Indico celery layer",
                "services": {
                    "indico-celery": {
                        "override": "replace",
                        "summary": "Indico celery",
                        "command": "/usr/local/bin/indico celery worker -B --uid 2000",
                        "startup": "enabled",
                        "user": "indico",
                        "environment": indico_env_config,
                    },
                },
            },
            "indico-nginx": {
                "summary": "Indico nginx layer",
                "description": "Indico nginx layer",
                "services": {
                    "indico-nginx": {
                        "override": "replace",
                        "summary": "Nginx service",
                        "command": "/usr/sbin/nginx",
                        "startup": "enabled",
                    },
                },
            },
        }
        return configuration[container_name]

    def _get_indico_env_config(self):
        """Return an envConfig with some core configuration."""
        redis_hostname = ""
        redis_port = ""
        for redis_unit in self._stored.redis_relation:
            redis_hostname = self._stored.redis_relation[redis_unit]["hostname"]
            redis_port = self._stored.redis_relation[redis_unit]["port"]

        env_config = {
            "CELERY_BROKER": "redis://{host}:{port}".format(host=redis_hostname, port=redis_port),
            "CUSTOMIZATION_DEBUG": self.config["customization_debug"],
            "INDICO_DB_URI": self._stored.db_uri,
            "INDICO_NO_REPLY_EMAIL": self.config["indico_no_reply_email"],
            "INDICO_PUBLIC_SUPPORT_EMAIL": self.config["indico_public_support_email"],
            "INDICO_SUPPORT_EMAIL": self.config["indico_support_email"],
            "REDIS_CACHE_URL": "redis://{host}:{port}".format(
                host=redis_hostname, port=redis_port
            ),
            "SECRET_KEY": self._stored.secret_key,
            "SERVICE_HOSTNAME": self._get_external_hostname(),
            "SERVICE_PORT": self._get_external_port(),
            "SERVICE_SCHEME": self._get_external_scheme(),
            "SMTP_LOGIN": self.config["smtp_login"],
            "SMTP_PASSWORD": self.config["smtp_password"],
            "SMTP_PORT": self.config["smtp_port"],
            "SMTP_SERVER": self.config["smtp_server"],
            "SMTP_USE_TLS": self.config["smtp_use_tls"],
        }
        return env_config

    def _on_config_changed(self, event):
        """Handle changes in configuration."""
        if self._are_relations_ready():
            if not self._are_pebble_instances_ready():
                self.unit.status = WaitingStatus("Waiting for pebble")
                event.defer()
                return

            self.model.unit.status = MaintenanceStatus("Configuring pod")
            for container_name in self.model.unit.containers:
                self._config_pebble(self.unit.get_container(container_name))

            self._download_customization_changes()
            self.ingress.update_config(self._make_ingress_config())
            self.model.unit.status = ActiveStatus()

    def _get_current_customization_url(self):
        """Get the current remote repository for the customization changes."""
        indico_container = self.unit.get_container("indico")
        process = indico_container.exec(
            ["git", "config", "--get", "remote.origin.url"],
            working_dir=INDICO_CUSTOMIZATION_DIR,
            user="indico",
        )
        remote_url = ""
        try:
            remote_url, _ = process.wait_output()
        except ExecError as ex:
            logging.debug(ex)
            pass
        return remote_url.rstrip()

    def _download_customization_changes(self):
        """Clone the remote repository with the customization changes."""
        current_remote_url = self._get_current_customization_url()
        if current_remote_url != self.config["customization_sources_url"]:
            logging.debug(
                "Removing old contents from directory %s. Previous repository: '%s'",
                INDICO_CUSTOMIZATION_DIR,
                current_remote_url,
            )
            indico_container = self.unit.get_container("indico")
            process = indico_container.exec(
                ["rm", "-rf", INDICO_CUSTOMIZATION_DIR],
                user="indico",
            )
            process.wait_output()
            process = indico_container.exec(
                ["mkdir", INDICO_CUSTOMIZATION_DIR],
                user="indico",
            )
            process.wait_output()
            if self.config["customization_sources_url"]:
                logging.debug(
                    "New URL repo for customization %s. Cloning contents",
                    self.config["customization_sources_url"],
                )
                process = indico_container.exec(
                    ["git", "clone", self.config["customization_sources_url"], "."],
                    working_dir=INDICO_CUSTOMIZATION_DIR,
                    user="indico",
                )
                process.wait_output()

    def _refresh_customization_changes(self, _):
        """Pull changes from the remote repository."""
        if self.config["customization_sources_url"]:
            logging.debug("Pulling changes from %s", self.config["customization_sources_url"])
            process = self.unit.get_container("indico").exec(
                ["git", "pull"],
                working_dir=INDICO_CUSTOMIZATION_DIR,
                user="indico",
            )
            process.wait_output()


if __name__ == "__main__":
    main(IndicoOperatorCharm)
