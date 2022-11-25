#!/usr/bin/env python3

# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm for Indico on kubernetes."""
import logging
import os
from re import findall
from typing import Dict, List, Tuple
from urllib.parse import urlparse

import ops.lib
from charms.grafana_k8s.v0.grafana_dashboard import GrafanaDashboardProvider
from charms.nginx_ingress_integrator.v0.ingress import IngressRequires
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider
from charms.redis_k8s.v0.redis import RedisRelationCharmEvents, RedisRequires
from ops.charm import ActionEvent, CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus
from ops.pebble import ExecError

DATABASE_NAME = "indico"
INDICO_CUSTOMIZATION_DIR = "/srv/indico/custom"
PORT = 8080
UBUNTU_SAML_URL = "https://login.ubuntu.com/saml/"
CANONICAL_LDAP_HOST = "ldap.canonical.com"
UWSGI_TOUCH_RELOAD = "/srv/indico/indico.wsgi"

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
            self.on.statsd_prometheus_exporter_pebble_ready, self._on_pebble_ready
        )
        self.framework.observe(
            self.on.refresh_external_resources_action, self._refresh_external_resources_action
        )
        # self.framework.observe(self.on.update_status, self._refresh_external_resources)

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
            self, jobs=[{"static_configs": [{"targets": ["*:9113", "*:9102"]}]}]
        )
        self._grafana_dashboards = GrafanaDashboardProvider(self)

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
        return urlparse(site_url).hostname if site_url else f"{self.app.name}.local"

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
        if not any(
            rel.app.name.startswith("redis-broker") for rel in self.model.relations["redis"]
        ):
            self.unit.status = WaitingStatus("Waiting for redis-broker availability")
            return False
        if not any(
            rel.app.name.startswith("redis-cache") for rel in self.model.relations["redis"]
        ):
            self.unit.status = WaitingStatus("Waiting for redis-cache availability")
            return False
        if not self._stored.db_uri:
            self.unit.status = WaitingStatus("Waiting for database availability")
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
        self.unit.status = MaintenanceStatus(f"Adding {container.name} layer to pebble")
        if container.name in ["indico", "indico-celery"]:
            plugins = (
                self.config["external_plugins"].split(",")
                if self.config["external_plugins"]
                else []
            )
            self._install_plugins(container, plugins)
        # The plugins need to be installed before adding the layer so that they are included in
        # the corresponding env vars
        pebble_config_func = getattr(
            self, f"_get_{container.name.replace('-', '_')}_pebble_config"
        )
        pebble_config = pebble_config_func(container)
        container.add_layer(container.name, pebble_config, combine=True)
        if container.name == "indico":
            self._download_customization_changes(container)
        self.unit.status = MaintenanceStatus(f"Starting {container.name} container")
        container.pebble.replan_services()
        if self._are_pebble_instances_ready():
            self.unit.set_workload_version(self._get_indico_version())
            self.unit.status = ActiveStatus()
        else:
            self.unit.status = WaitingStatus("Waiting for pebble")

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
                    "command": "/srv/indico/.local/bin/indico celery worker -B",
                    "startup": "enabled",
                    "user": "indico",
                    "environment": indico_env_config,
                },
            },
            "checks": {
                "ready": {
                    "override": "replace",
                    "level": "alive",
                    "period": "120s",
                    "timeout": "119s",
                    "exec": {
                        "command": "/srv/indico/.local/bin/indico celery inspect ping",
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
                "nginx-exporter": {
                    "override": "replace",
                    "summary": "Nginx Exporter",
                    "command": (
                        "nginx-prometheus-exporter"
                        " -nginx.scrape-uri=http://localhost:9080/stub_status"
                    ),
                    "startup": "enabled",
                },
            },
            "checks": {
                "nginx-exporter-up": {
                    "override": "replace",
                    "level": "alive",
                    "http": {"url": "http://localhost:9113/metrics"},
                },
            },
        }

    def _get_statsd_prometheus_exporter_pebble_config(self, _):
        """Generate pebble config for the statsd-prometheus-exporter container.

        Returns:
            The pebble configuration for the container.
        """
        return {
            "summary": "Statsd prometheus exporter",
            "description": "Prometheus exporter for statsd",
            "services": {
                "statsd-exporter": {
                    "override": "replace",
                    "summary": "Statsd Exporter",
                    "command": ("statsd_exporter"),
                    "startup": "enabled",
                },
            },
            "checks": {
                "statsd-exporter-up": {
                    "override": "replace",
                    "level": "alive",
                    "http": {"url": "http://localhost:9102/metrics"},
                },
            },
        }

    def _get_indico_env_config(self, container):
        """Return an envConfig with some core configuration."""
        cache_rel = next(
            rel for rel in self.model.relations["redis"] if rel.app.name.startswith("redis-cache")
        )
        cache_unit = next(unit for unit in cache_rel.data if unit.name.startswith("redis-cache"))
        cache_host = cache_rel.data[cache_unit].get("hostname")
        cache_port = cache_rel.data[cache_unit].get("port")

        broker_rel = next(
            rel for rel in self.model.relations["redis"] if rel.app.name.startswith("redis-broker")
        )
        broker_unit = next(
            unit for unit in broker_rel.data if unit.name.startswith("redis-broker")
        )
        broker_host = broker_rel.data[broker_unit].get("hostname")
        broker_port = broker_rel.data[broker_unit].get("port")

        available_plugins = []
        process = container.exec(
            ["/srv/indico/.local/bin/indico", "setup", "list-plugins"],
            user="indico",
        )
        output, _ = process.wait_output()
        # Parse output table, discarding header and footer rows and fetching first column value
        available_plugins = [item.split("|")[1].strip() for item in output.split("\n")[3:-2]]

        peer_relation = self.model.get_relation("indico-peers")
        env_config = {
            "ATTACHMENT_STORAGE": "default",
            "CELERY_BROKER": f"redis://{broker_host}:{broker_port}",
            "CUSTOMIZATION_DEBUG": self.config["customization_debug"],
            "ENABLE_ROOMBOOKING": self.config["enable_roombooking"],
            "INDICO_AUTH_PROVIDERS": str({}),
            "INDICO_DB_URI": self._stored.db_uri,
            "INDICO_EXTRA_PLUGINS": ",".join(available_plugins),
            "INDICO_IDENTITY_PROVIDERS": str({}),
            "INDICO_NO_REPLY_EMAIL": self.config["indico_no_reply_email"],
            "INDICO_PUBLIC_SUPPORT_EMAIL": self.config["indico_public_support_email"],
            "INDICO_SUPPORT_EMAIL": self.config["indico_support_email"],
            "REDIS_CACHE_URL": f"redis://{cache_host}:{cache_port}",
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
                    "x509cert": (
                        "MIICjzCCAfigAwIBAgIJALNN/vxaR1hyMA0GCSqGSIb3DQEBBQUAMDoxCzAJBgNVBAYTAkdCM"
                        "RMwEQYDVQQIEwpTb21lLVN0YXRlMRYwFAYDVQQKEw1DYW5vbmljYWwgTHRkMB4XDTEyMDgxMD"
                        "EyNDE0OFoXDTEzMDgxMDEyNDE0OFowOjELMAkGA1UEBhMCR0IxEzARBgNVBAgTClNvbWUtU3R"
                        "hdGUxFjAUBgNVBAoTDUNhbm9uaWNhbCBMdGQwgZ8wDQYJKoZIhvcNAQEBBQADgY0AMIGJAoGB"
                        "AMM4pmIxkv419q8zj5EojK57y6plU/+k3apX6w1PgAYeI0zhNuud/tiqKVQEDyZ6W7HNeGtWS"
                        "h5rewy8c07BShcHG5Y8ibzBdIibGs5k6gvtmsRiXDE/F39+RrPSW18beHhEuoVJM9RANp3MYM"
                        "OK11SiClSiGo+NfBKFuoqNX3UjAgMBAAGjgZwwgZkwHQYDVR0OBBYEFH/no88pbywRnW6Fz+B"
                        "4lQ04w/86MGoGA1UdIwRjMGGAFH/no88pbywRnW6Fz+B4lQ04w/86oT6kPDA6MQswCQYDVQQG"
                        "EwJHQjETMBEGA1UECBMKU29tZS1TdGF0ZTEWMBQGA1UEChMNQ2Fub25pY2FsIEx0ZIIJALNN/"
                        "vxaR1hyMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcNAQEFBQADgYEArTGbZ1rg++aBxnNuJ7eho6"
                        "2JKKtRW5O+kMBvBLWi7fKck5uXDE6d7Jv6hUy/gwUZV7r5kuPwRlw3Pu6AX4R60UsQuVG1/VV"
                        "VI7nu32iCkXx5Vzq446IkVRdk/QOda1dRyq0oaifUUhJfwVFSsm95ENDFdGqD0raj7g77ajcB"
                        "Mf8="
                    ),
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
            if self.config["ldap_host"]:
                _ldap_config = {
                    "uri": f"ldaps://{self.config['ldap_host']}",
                    "bind_dn": "cn=Indico Bot,ou=bots,dc=canonical,dc=com",
                    "bind_password": self.config["ldap_password"],
                    "timeout": 30,
                    "verify_cert": True,
                    "page_size": 1500,
                    "uid": "cn", # launchpadID
                    "user_base": "ou=staff,dc=canonical,dc=com",
                    "user_filter": "(objectClass=canonicalPerson)",
                    "gid": "ou",
                    "group_base": "dc=canonical,dc=com",
                    "group_filter": "(objectClass=organizationalRole)",
                    "member_of_attr": "ou",
                    "ad_group_style": True,
                }
                identity_providers = {
                    "ubuntu": {
                        "type": "ldap",
                        "title": "LDAP",
                        "ldap": _ldap_config,
                        "mapping": {
                            "email": "mail",
                            "affiliation": "company",
                            "first_name": "givenName",
                            "last_name": "sn",
                            "phone": "mobile",
                        },
                        "trusted_email": True,
                        "synced_fields": {"first_name", "last_name", "affiliation", "phone"}
                    }
                }
                provider_map = {
                    'ubuntu': {'identity_provider': 'ubuntu', 'mapping': {'identifier': 'username'}}
                }
                env_config["INDICO_PROVIDER_MAP"] = str(provider_map)
            env_config["INDICO_IDENTITY_PROVIDERS"] = str(identity_providers)
            
            env_config = {**env_config, **self._get_http_proxy_configuration()}
        return env_config

    def _get_http_proxy_configuration(self):
        """Generate http proxy config."""
        config = {}
        if self.config["http_proxy"]:
            config["HTTP_PROXY"] = self.config["http_proxy"]
        if self.config["https_proxy"]:
            config["HTTPS_PROXY"] = self.config["https_proxy"]
        return config

    def _is_ldap_host_valid(self) -> bool:
        """Check if the LDAP hostis currently supported."""
        return (
            not self.config["ldap_host"] or CANONICAL_LDAP_HOST == self.config["ldap_host"]
        )

    def _is_saml_target_url_valid(self) -> bool:
        """Check if the target SAML URL is currently supported."""
        return (
            not self.config["saml_target_url"] or UBUNTU_SAML_URL == self.config["saml_target_url"]
        )

    def _on_config_changed(self, event):
        """Handle changes in configuration."""
        if not self._is_saml_target_url_valid():
            self.unit.status = BlockedStatus(
                f"Invalid saml_target_url option provided. Only {UBUNTU_SAML_URL} is available."
            )
            event.defer()
            return
        if not self._is_ldap_host_valid():
            self.unit.status = BlockedStatus(
                f"Invalid ldap_host option provided. Only {CANONICAL_LDAP_HOST} is available."
            )
            event.defer()
            return
        if not self._are_relations_ready(event):
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

    def _get_current_customization_url(self) -> str:
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
                ["pip", "install", "--upgrade"] + plugins,
                environment=self._get_http_proxy_configuration(),
            )
            process.wait_output()

    def _get_indico_version(self):
        container = self.unit.get_container("indico")
        process = container.exec(
            ["/srv/indico/.local/bin/indico", "--version"],
            user="indico",
        )
        version_string, _ = process.wait_output()
        version = findall("[0-9.]+", version_string)
        return version[0] if version else ""

    def _exec_cmd_in_custom_dir(self, container, command: List[str]):
        """Execute command in indico customization directory.

        Args:
            container: container in a unit where the command will be executed
            command: command to execute. The first item is the name (or path)
                    of the executable, the rest of the items are the arguments.
        """
        process = container.exec(
            command,
            working_dir=INDICO_CUSTOMIZATION_DIR,
            user="indico",
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
                self._exec_cmd_in_custom_dir(
                    container, ["git", "clone", self.config["customization_sources_url"], "."]
                )

    def _refresh_external_resources(self, _) -> Dict:
        """Pull changes from the remote repository and upgrade external plugins."""
        results = {
            "customization-changes": False,
            "plugin-updates": [],
        }
        container = self.unit.get_container("indico")
        if container.can_connect():
            self._download_customization_changes(container)
            if self.config["customization_sources_url"]:
                logging.debug("Pulling changes from %s", self.config["customization_sources_url"])
                self._exec_cmd_in_custom_dir(
                    container,
                    ["git", "pull"],
                )
                logging.debug("Reloading uWSGI")
                self._exec_cmd_in_custom_dir(container, ["touch", UWSGI_TOUCH_RELOAD])
                results["customization-changes"] = True
            if self.config["external_plugins"]:
                logging.debug("Upgrading external plugins %s", self.config["external_plugins"])
                plugins = self.config["external_plugins"].split(",")
                self._install_plugins(container, plugins)
                results["plugin-updates"] = plugins
        return results

    def _refresh_external_resources_action(self, event: ActionEvent) -> None:
        """Refresh external resources and report action result."""
        results = self._refresh_external_resources(event)
        event.set_results(results)

    def _on_leader_elected(self, _) -> None:
        """Handle leader-elected event."""
        peer_relation = self.model.get_relation("indico-peers")
        if not peer_relation.data[self.app].get("secret-key"):
            peer_relation.data[self.app].update({"secret-key": repr(os.urandom(32))})


if __name__ == "__main__":  # pragma: no cover
    main(IndicoOperatorCharm, use_juju_for_storage=True)
