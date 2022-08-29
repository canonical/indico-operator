#!/usr/bin/env python3

# Copyright 2022 Canonical Ltd.
# Licensed under the GPLv3, see LICENCE file for details.

"""Charm for Indico on kubernetes."""
import logging
import os
from typing import Tuple
from urllib.parse import urlparse

import ops.lib
from charms.nginx_ingress_integrator.v0.ingress import IngressRequires
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider
from charms.redis_k8s.v0.redis import RedisRelationCharmEvents, RedisRequires
from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus
from ops.pebble import ExecError

DATABASE_NAME = "indico"
INDICO_CUSTOMIZATION_DIR = "/srv/indico/custom"
PORT = 8080
UBUNTU_SAML_URL = "https://login.ubuntu.com/saml/"

pgsql = ops.lib.use("pgsql", 1, "postgresql-charmers@lists.launchpad.net")


class IndicoOperatorCharm(CharmBase):
    """Charm for Indico on kubernetes."""

    _stored = StoredState()
    on = RedisRelationCharmEvents()

    def __init__(self, *args):
        super().__init__(*args)

        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.leader_elected, self._on_leader_elected)
        self.framework.observe(self.on.indico_pebble_ready, self._on_pebble_ready)
        self.framework.observe(self.on.indico_celery_pebble_ready, self._on_pebble_ready)
        self.framework.observe(self.on.indico_nginx_pebble_ready, self._on_pebble_ready)
        self.framework.observe(
            self.on.nginx_prometheus_exporter_pebble_ready, self._on_pebble_ready
        )
        self.framework.observe(
            self.on.refresh_customization_changes_action, self._refresh_customization_changes
        )

        self._stored.set_default(
            db_conn_str=None,
            db_uri=None,
            db_ro_uris=[],
            redis_relation={},
        )

        self.db = pgsql.PostgreSQLClient(self, "db")
        self.framework.observe(
            self.db.on.database_relation_joined, self._on_database_relation_joined
        )
        self.framework.observe(self.db.on.master_changed, self._on_master_changed)

        self.redis = RedisRequires(self, self._stored)
        self.framework.observe(self.on.redis_relation_changed, self._on_config_changed)

        self.ingress = IngressRequires(self, self._make_ingress_config())
        self._metrics_endpoint = MetricsEndpointProvider(
            self, jobs=[{"static_configs": [{"targets": ["*:9113"]}]}]
        )

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
        return all(
            [
                self.unit.get_container(container_name).can_connect()
                for container_name in self.model.unit.containers
            ]
        )

    def _is_configuration_valid(self) -> Tuple[bool, str]:
        """Validate charm configuration."""
        site_url = self.config["site_url"]
        if site_url and not urlparse(site_url).hostname:
            return False, "Configuration option site_url is not valid"
        return True, ""

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

    def _are_relations_ready(self, _):
        """Handle the on pebble ready event for Indico."""
        if not any(rel.app.name == "redis-broker" for rel in self.model.relations["redis"]):
            self.unit.status = WaitingStatus("Waiting for redis-broker relation")
            return False
        if not any(rel.app.name == "redis-cache" for rel in self.model.relations["redis"]):
            self.unit.status = WaitingStatus("Waiting for redis-cache relation")
            return False
        if not self._stored.db_uri:
            self.unit.status = WaitingStatus("Waiting for database relation")
            return False
        return True

    def _on_pebble_ready(self, event):
        """Handle the on pebble ready event for the containers."""
        if not self._are_relations_ready(event) or not event.workload.can_connect():
            event.defer()
            return
        self._config_pebble(event.workload)

    def _config_pebble(self, container):
        """Apply pebble changes."""
        pebble_config_func = getattr(
            self, "_get_{}_pebble_config".format(container.name.replace("-", "_"))
        )
        pebble_config = pebble_config_func(container)
        self.unit.status = MaintenanceStatus("Adding {} layer to pebble".format(container.name))
        container.add_layer(container.name, pebble_config, combine=True)
        for container.name in ["indico", "indico-celery"]:
            self._set_git_proxy_config(container)
            plugins = (
                self.config["external_plugins"].split(",")
                if self.config["external_plugins"]
                else []
            )
            if self.config["s3_storage"]:
                plugins.append("indico-plugin-storage-s3")
            self._install_plugins(container, plugins)
        if container.name == "indico":
            self._download_customization_changes(container)
        self.unit.status = MaintenanceStatus("Starting {} container".format(container.name))
        container.pebble.replan_services()
        if self._are_pebble_instances_ready():
            self.unit.status = ActiveStatus()
        else:
            self.unit.status = WaitingStatus("Waiting for pebble")

    def _set_git_proxy_config(self, container):
        """Set git proxy configuration in indico and indico-celery containers."""
        # Workaround for pip issue https://github.com/pypa/pip/issues/11405
        git_config_http_command = ["git", "config", "--global", "--unset", "http.proxy"]
        git_config_https_command = ["git", "config", "--global", "--unset", "https.proxy"]
        if self.config["http_proxy"]:
            git_config_http_command = [
                "git",
                "config",
                "--global",
                "http.proxy",
                self.config["http_proxy"],
            ]
        if self.config["https_proxy"]:
            git_config_https_command = [
                "git",
                "config",
                "--global",
                "http.proxy",
                self.config["https_proxy"],
            ]

        process = container.exec(git_config_http_command)
        # Workaround for the git config --unset command not being idempotent. It returns a '5'
        # error code when the configuration has not being set
        try:
            process.wait_output()
        except ExecError as ex:
            if ex.exit_code != 5:
                raise ex
        process = container.exec(git_config_https_command)
        try:
            process.wait_output()
        except ExecError as ex:
            if ex.exit_code != 5:
                raise ex

    def _get_indico_pebble_config(self, container):
        """Generate pebble config for the indico container."""
        indico_env_config = self._get_indico_env_config(container)
        return {
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
            "checks": {
                "indico-ready": {
                    "override": "replace",
                    "level": "ready",
                    "tcp": {"port": 8081},
                }
            },
        }

    def _get_indico_celery_pebble_config(self, container):
        """Generate pebble config for the indico-celery container."""
        indico_env_config = self._get_indico_env_config(container)
        return {
            "summary": "Indico celery layer",
            "description": "Indico celery layer",
            "services": {
                "indico-celery": {
                    "override": "replace",
                    "summary": "Indico celery",
                    "command": "/usr/local/bin/indico celery worker -B",
                    "startup": "enabled",
                    "user": "indico",
                    "environment": indico_env_config,
                },
            },
            "checks": {
                "ready": {
                    "override": "replace",
                    "level": "alive",
                    "period": "20s",
                    "timeout": "19s",
                    "exec": {
                        "command": "/usr/local/bin/indico celery inspect ping",
                        "environment": indico_env_config,
                    },
                },
            },
        }

    def _get_indico_nginx_pebble_config(self, _):
        """Generate pebble config for the indico-nginx container."""
        return {
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
            "checks": {
                "nginx-up": {
                    "override": "replace",
                    "level": "ready",
                    "exec": {"command": "service nginx status"},
                },
                "nginx-ready": {
                    "override": "replace",
                    "level": "alive",
                    "http": {"url": "http://localhost:8080/health"},
                },
            },
        }

    def _get_nginx_prometheus_exporter_pebble_config(self, _):
        """Generate pebble config for the nginx-prometheus-exporter container."""
        return {
            "summary": "Nginx prometheus exporter",
            "description": "Prometheus exporter for nginx",
            "services": {
                "exporter": {
                    "override": "replace",
                    "summary": "Exporter",
                    "command": "nginx-prometheus-exporter -nginx.scrape-uri=http://localhost:9080/stub_status",
                    "startup": "enabled",
                },
            },
            "checks": {
                "exporter-up": {
                    "override": "replace",
                    "level": "alive",
                    "http": {"url": "http://localhost:9113/metrics"},
                },
            },
        }

    def _get_indico_env_config(self, container):
        """Return an envConfig with some core configuration."""
        cache_rel = next(
            rel for rel in self.model.relations["redis"] if rel.app.name == "redis-cache"
        )
        cache_host = self._stored.redis_relation[cache_rel.id]["hostname"]
        cache_port = self._stored.redis_relation[cache_rel.id]["port"]

        broker_rel = next(
            rel for rel in self.model.relations["redis"] if rel.app.name == "redis-broker"
        )
        broker_host = self._stored.redis_relation[broker_rel.id]["hostname"]
        broker_port = self._stored.redis_relation[broker_rel.id]["port"]

        available_plugins = []
        process = container.exec(["indico", "setup", "list-plugins"])
        output, _ = process.wait_output()
        # Parse output table, discarding header and footer rows and fetching first column value
        available_plugins = [item.split("|")[1].strip() for item in output.split("\n")[3:-2]]

        peer_relation = self.model.get_relation("indico-peers")
        env_config = {
            "ATTACHMENT_STORAGE": "default",
            "CELERY_BROKER": "redis://{host}:{port}".format(host=broker_host, port=broker_port),
            "CUSTOMIZATION_DEBUG": self.config["customization_debug"],
            "INDICO_AUTH_PROVIDERS": str({}),
            "INDICO_DB_URI": self._stored.db_uri,
            "INDICO_EXTRA_PLUGINS": ",".join(available_plugins),
            "INDICO_IDENTITY_PROVIDERS": str({}),
            "INDICO_NO_REPLY_EMAIL": self.config["indico_no_reply_email"],
            "INDICO_PUBLIC_SUPPORT_EMAIL": self.config["indico_public_support_email"],
            "INDICO_SUPPORT_EMAIL": self.config["indico_support_email"],
            "REDIS_CACHE_URL": "redis://{host}:{port}".format(host=cache_host, port=cache_port),
            "SECRET_KEY": peer_relation.data[self.app].get("secret-key"),
            "SERVICE_HOSTNAME": self._get_external_hostname(),
            "SERVICE_PORT": self._get_external_port(),
            "SERVICE_SCHEME": self._get_external_scheme(),
            "SMTP_LOGIN": self.config["smtp_login"],
            "SMTP_PASSWORD": self.config["smtp_password"],
            "SMTP_PORT": self.config["smtp_port"],
            "SMTP_SERVER": self.config["smtp_server"],
            "SMTP_USE_TLS": self.config["smtp_use_tls"],
            "STORAGE_DICT": {
                "default": "fs:/srv/indico/archive",
            },
        }

        # Piwik settings can't be configured using the config file for the time being:
        # https://github.com/indico/indico-plugins/issues/182
        if self.config["s3_storage"]:
            env_config["STORAGE_DICT"].update({"s3": self.config["s3_storage"]})
            env_config["ATTACHMENT_STORAGE"] = "s3"
        env_config["STORAGE_DICT"] = str(env_config["STORAGE_DICT"])

        # SAML configuration reference https://github.com/onelogin/python3-saml
        if self.config["saml_target_url"]:
            saml_config = {
                "strict": True,
                "sp": {
                    "entityId": self.config["site_url"],
                },
                "idp": {
                    "entityId": "https://login.ubuntu.com",
                    "singleSignOnService": {
                        "url": "https://login.ubuntu.com/saml/",
                        "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                    },
                    "singleLogoutService": {
                        "url": "https://login.ubuntu.com/+logout",
                        "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                    },
                    "x509cert": "MIICjzCCAfigAwIBAgIJALNN/vxaR1hyMA0GCSqGSIb3DQEBBQUAMDoxCzAJBgNVBAYTAkdCMRMwEQYDVQQIEwpTb21lLVN0YXRlMRYwFAYDVQQKEw1DYW5vbmljYWwgTHRkMB4XDTEyMDgxMDEyNDE0OFoXDTEzMDgxMDEyNDE0OFowOjELMAkGA1UEBhMCR0IxEzARBgNVBAgTClNvbWUtU3RhdGUxFjAUBgNVBAoTDUNhbm9uaWNhbCBMdGQwgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBAMM4pmIxkv419q8zj5EojK57y6plU/+k3apX6w1PgAYeI0zhNuud/tiqKVQEDyZ6W7HNeGtWSh5rewy8c07BShcHG5Y8ibzBdIibGs5k6gvtmsRiXDE/F39+RrPSW18beHhEuoVJM9RANp3MYMOK11SiClSiGo+NfBKFuoqNX3UjAgMBAAGjgZwwgZkwHQYDVR0OBBYEFH/no88pbywRnW6Fz+B4lQ04w/86MGoGA1UdIwRjMGGAFH/no88pbywRnW6Fz+B4lQ04w/86oT6kPDA6MQswCQYDVQQGEwJHQjETMBEGA1UECBMKU29tZS1TdGF0ZTEWMBQGA1UEChMNQ2Fub25pY2FsIEx0ZIIJALNN/vxaR1hyMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcNAQEFBQADgYEArTGbZ1rg++aBxnNuJ7eho62JKKtRW5O+kMBvBLWi7fKck5uXDE6d7Jv6hUy/gwUZV7r5kuPwRlw3Pu6AX4R60UsQuVG1/VVVI7nu32iCkXx5Vzq446IkVRdk/QOda1dRyq0oaifUUhJfwVFSsm95ENDFdGqD0raj7g77ajcBMf8=",
                },
            }
            auth_providers = {"ubuntu": {"type": "saml", "saml_config": saml_config}}
            env_config["INDICO_AUTH_PROVIDERS"] = str(auth_providers)
            identity_providers = {
                "ubuntu": {
                    "type": "saml",
                    "trusted_email": True,
                    "mapping": {
                        "user_name": "username",
                        "first_name": "fullname",
                        "last_name": "",
                        "email": "email",
                    },
                    "identifier_field": "openid",
                }
            }
            env_config["INDICO_IDENTITY_PROVIDERS"] = str(identity_providers)
        return env_config

    def _get_http_proxy_configuration(self):
        """Generate http proxy config."""
        config = {}
        if self.config["http_proxy"]:
            config["HTTP_PROXY"] = self.config["http_proxy"]
        if self.config["https_proxy"]:
            config["HTTPS_PROXY"] = self.config["https_proxy"]
        return config if config else None

    def _is_saml_target_url_valid(self):
        """Check if the target SAML URL is currently supported."""
        return (
            not self.config["saml_target_url"] or UBUNTU_SAML_URL == self.config["saml_target_url"]
        )

    def _on_config_changed(self, event):
        """Handle changes in configuration."""
        if not self._are_relations_ready(event):
            event.defer()
            return
        if not self._is_saml_target_url_valid():
            self.unit.status = BlockedStatus(
                "Invalid saml_target_url option provided. Only {} is available.".format(
                    UBUNTU_SAML_URL
                )
            )
            event.defer()
            return
        if not self._are_pebble_instances_ready():
            self.unit.status = WaitingStatus("Waiting for pebble")
            event.defer()
            return
        self.model.unit.status = MaintenanceStatus("Configuring pod")
        is_valid, error = self._is_configuration_valid()
        if not is_valid:
            self.model.unit.status = BlockedStatus(error)
            event.defer()
            return
        for container_name in self.model.unit.containers:
            self._config_pebble(self.unit.get_container(container_name))
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

    def _install_plugins(self, container, plugins):
        """Install the external plugins."""
        if plugins:
            process = container.exec(
                ["python3.9", "-m", "pip", "install"] + plugins,
                environment=self._get_http_proxy_configuration(),
            )
            process.wait_output()

    def _download_customization_changes(self, container):
        """Clone the remote repository with the customization changes."""
        current_remote_url = self._get_current_customization_url()
        if current_remote_url != self.config["customization_sources_url"]:
            logging.debug(
                "Removing old contents from directory %s. Previous repository: '%s'",
                INDICO_CUSTOMIZATION_DIR,
                current_remote_url,
            )
            process = container.exec(
                ["rm", "-rf", INDICO_CUSTOMIZATION_DIR],
                user="indico",
            )
            process.wait_output()
            process = container.exec(
                ["mkdir", INDICO_CUSTOMIZATION_DIR],
                user="indico",
            )
            process.wait_output()
            if self.config["customization_sources_url"]:
                logging.debug(
                    "New URL repo for customization %s. Cloning contents",
                    self.config["customization_sources_url"],
                )
                process = container.exec(
                    ["git", "clone", self.config["customization_sources_url"], "."],
                    working_dir=INDICO_CUSTOMIZATION_DIR,
                    user="indico",
                    environment=self._get_http_proxy_configuration(),
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
                environment=self._get_http_proxy_configuration(),
            )
            process.wait_output()

    def _on_leader_elected(self, _) -> None:
        """Handle leader-elected event."""
        peer_relation = self.model.get_relation("indico-peers")
        if not peer_relation.data[self.app].get("secret-key"):
            peer_relation.data[self.app].update({"secret-key": repr(os.urandom(32))})


if __name__ == "__main__":  # pragma: no cover
    main(IndicoOperatorCharm, use_juju_for_storage=True)
