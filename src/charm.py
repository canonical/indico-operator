#!/usr/bin/env python3

# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm for Indico on kubernetes."""
import logging
import os
import typing
from re import findall
from typing import Dict, Iterator, List, Optional, Tuple
from urllib.parse import urlparse

import ops.lib
from charms.grafana_k8s.v0.grafana_dashboard import GrafanaDashboardProvider
from charms.nginx_ingress_integrator.v0.nginx_route import require_nginx_route
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider
from charms.redis_k8s.v0.redis import RedisRelationCharmEvents, RedisRequires
from ops.charm import ActionEvent, CharmBase, HookEvent, PebbleReadyEvent
from ops.framework import StoredState
from ops.jujuversion import JujuVersion
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, Container, MaintenanceStatus, WaitingStatus
from ops.pebble import ExecError

from database_observer import DatabaseObserver
from smtp_observer import SmtpObserver
from state import CharmConfigInvalidError, ProxyConfig, State

logger = logging.getLogger(__name__)

CELERY_PROMEXP_PORT = "9808"
DATABASE_NAME = "indico"
EMAIL_LIST_MAX = 50
EMAIL_LIST_SEPARATOR = ","
INDICO_CUSTOMIZATION_DIR = "/srv/indico/custom"
NGINX_PROMEXP_PORT = "9113"
PORT = 8080
STATSD_PROMEXP_PORT = "9102"
UBUNTU_SAML_URL = "https://login.ubuntu.com/saml/"
STAGING_UBUNTU_SAML_URL = "https://login.staging.ubuntu.com/saml/"
SAML_GROUPS_PLUGIN_NAME = "saml_groups"

UWSGI_TOUCH_RELOAD = "/srv/indico/indico.wsgi"


class IndicoOperatorCharm(CharmBase):
    """Charm for Indico on kubernetes.

    Attrs:
        on: Redis relation charm events.
    """

    _stored = StoredState()
    on = RedisRelationCharmEvents()

    def __init__(self, *args):
        """Construct.

        Args:
            args: Arguments passed to the CharmBase parent constructor.
        """
        super().__init__(*args)
        self.database = DatabaseObserver(self)
        self.smtp = SmtpObserver(self)
        try:
            self.state = State.from_charm(
                self, smtp_relation_data=self.smtp.smtp.get_relation_data()
            )
        except CharmConfigInvalidError as exc:
            self.unit.status = ops.BlockedStatus(exc.msg)
            return
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.leader_elected, self._on_leader_elected)
        self.framework.observe(self.on.indico_pebble_ready, self._on_pebble_ready)
        self.framework.observe(self.on.indico_celery_pebble_ready, self._on_pebble_ready)
        self.framework.observe(self.on.indico_nginx_pebble_ready, self._on_pebble_ready)
        self.framework.observe(
            self.on.refresh_external_resources_action, self._refresh_external_resources_action
        )
        # self.framework.observe(self.on.update_status, self._refresh_external_resources)
        self.framework.observe(self.on.add_admin_action, self._add_admin_action)
        self.framework.observe(self.on.anonymize_user_action, self._anonymize_user_action)

        # Still needed by the library
        self._stored.set_default(
            redis_relation={},
        )

        self.redis_broker = RedisRequires(self, self._stored, "redis-broker")
        self.framework.observe(
            self.redis_broker.charm.on.redis_relation_updated, self._on_config_changed
        )
        self.redis_cache = RedisRequires(self, self._stored, "redis-cache")
        self.framework.observe(
            self.redis_cache.charm.on.redis_relation_updated, self._on_config_changed
        )
        self._require_nginx_route()

        self._metrics_endpoint = MetricsEndpointProvider(
            self,
            jobs=[
                {
                    "static_configs": [
                        {
                            "targets": [
                                f"*:{NGINX_PROMEXP_PORT}",
                                f"*:{STATSD_PROMEXP_PORT}",
                                f"*:{CELERY_PROMEXP_PORT}",
                            ]
                        }
                    ]
                }
            ],
        )
        self._grafana_dashboards = GrafanaDashboardProvider(self)

    def _require_nginx_route(self) -> None:
        """Require nginx ingress."""
        require_nginx_route(
            charm=self,
            service_hostname=self._get_external_hostname(),
            service_name=self.app.name,
            service_port=8080,
        )

    def _are_pebble_instances_ready(self) -> bool:
        """Check if all pebble instances are up and containers available.

        Returns:
            If the containers are up and available.
        """
        return all(
            self.unit.get_container(container_name).can_connect()
            for container_name in self.model.unit.containers
        )

    def _is_configuration_valid(self) -> Tuple[bool, str]:
        """Validate charm configuration.

        Returns:
            Tuple containing as first element whether the configuration is valid.
            and a string with the error, if any, as second element.
        """
        site_url = self.config["site_url"]
        if site_url and not urlparse(site_url).hostname:
            return False, "Configuration option site_url is not valid"
        return True, ""

    def _get_external_hostname(self) -> str:
        """Extract and return hostname from site_url or default to [application name].local.

        Returns:
            The site URL defined as part of the site_url configuration or a default value.
        """
        site_url = self.config["site_url"]
        if not site_url or not (hostname := urlparse(site_url).hostname):
            return f"{self.app.name}.local"
        return hostname

    def _get_external_scheme(self) -> str:
        """Extract and return schema from site_url.

        Returns:
            The HTTP schema.
        """
        site_url = self.config["site_url"]
        return urlparse(site_url).scheme if site_url else "http"

    def _get_external_port(self) -> Optional[int]:
        """Extract and return port from site_url.

        Returns:
            The port number.
        """
        site_url = self.config["site_url"]
        return urlparse(site_url).port

    def _are_relations_ready(self, _) -> bool:
        """Check if the needed relations are established.

        Returns:
            If the needed relations have been established.
        """
        if self.redis_broker.relation_data is None:
            self.unit.status = WaitingStatus("Waiting for redis-broker availability")
            return False
        if self.redis_cache.relation_data is None:
            self.unit.status = WaitingStatus("Waiting for redis-cache availability")
            return False
        if self.database.uri is None:
            self.unit.status = WaitingStatus("Waiting for database availability")
            return False
        return True

    def _on_pebble_ready(self, event: PebbleReadyEvent) -> None:
        """Handle the on pebble ready event for the containers.

        Args:
            event: Event triggering the pebble ready handler.
        """
        if not self._are_relations_ready(event) or not event.workload.can_connect():
            event.defer()
            return
        self._config_pebble(event.workload)

    def _config_pebble(self, container: Container) -> None:
        """Apply pebble configurations to a container.

        Args:
            container: Container to be configured by Pebble.
        """
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
            celery_config = self._get_celery_prometheus_exporter_pebble_config(container)
            statsd_config = self._get_statsd_prometheus_exporter_pebble_config(container)
            container.add_layer("celery", celery_config, combine=True)
            container.add_layer("statsd", statsd_config, combine=True)
            self._download_customization_changes(container)
        if container.name == "indico-nginx":
            pebble_config = self._get_nginx_prometheus_exporter_pebble_config(container)
            container.add_layer("nginx", pebble_config, combine=True)
        self.unit.status = MaintenanceStatus(f"Starting {container.name} container")
        container.pebble.replan_services()
        if self._are_pebble_instances_ready():
            self.unit.set_workload_version(self._get_indico_version())
            self.unit.status = ActiveStatus()
        else:
            self.unit.status = WaitingStatus("Waiting for pebble")

    def _get_indico_pebble_config(self, container: Container) -> ops.pebble.LayerDict:
        """Generate pebble config for the indico container.

        Args:
            container: Indico container that has the target configuration.

        Returns:
            The pebble configuration for the container.
        """
        indico_env_config = self._get_indico_env_config(container)
        layer = {
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
                },
            },
        }
        return typing.cast(ops.pebble.LayerDict, layer)

    def _get_indico_celery_pebble_config(self, container: Container) -> Dict:
        """Generate pebble config for the indico-celery container.

        Args:
            container: Celery container that has the target configuration.

        Returns:
            The pebble configuration for the container.
        """
        indico_env_config = self._get_indico_env_config(container)
        return {
            "summary": "Indico celery layer",
            "description": "Indico celery layer",
            "services": {
                "indico-celery": {
                    "override": "replace",
                    "summary": "Indico celery",
                    "command": "/usr/local/bin/indico celery worker -B -E",
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
                        "command": "/usr/local/bin/indico celery inspect ping",
                        "environment": indico_env_config,
                    },
                },
            },
        }

    def _get_indico_nginx_pebble_config(self, _) -> Dict:
        """Generate pebble config for the indico-nginx container.

        Returns:
            The pebble configuration for the container.
        """
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
                "nginx-ready": {
                    "override": "replace",
                    "level": "alive",
                    "http": {"url": "http://localhost:8080/health"},
                },
            },
        }

    def _get_celery_prometheus_exporter_pebble_config(self, container) -> ops.pebble.LayerDict:
        """Generate pebble config for the celery-prometheus-exporter container.

        Args:
            container: Celery container that has the target configuration.

        Returns:
            The pebble configuration for the container.
        """
        indico_env_config = self._get_indico_env_config(container)
        layer = {
            "summary": "Celery prometheus exporter",
            "description": "Prometheus exporter for celery",
            "services": {
                "celery-exporter": {
                    "override": "replace",
                    "summary": "Celery Exporter",
                    "command": (
                        "celery-exporter"
                        f" --broker-url={self.redis_broker.url}"
                        " --retry-interval=5"
                    ),
                    "environment": indico_env_config,
                    "startup": "enabled",
                },
            },
            "checks": {
                "celery-exporter-up": {
                    "override": "replace",
                    "level": "alive",
                    "http": {"url": "http://localhost:9808/health"},
                },
            },
        }
        return typing.cast(ops.pebble.LayerDict, layer)

    def _get_nginx_prometheus_exporter_pebble_config(self, _) -> ops.pebble.LayerDict:
        """Generate pebble config for the nginx-prometheus-exporter container.

        Returns:
            The pebble configuration for the container.
        """
        layer = {
            "summary": "Nginx prometheus exporter",
            "description": "Prometheus exporter for nginx",
            "services": {
                "nginx-prometheus-exporter": {
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
        return typing.cast(ops.pebble.LayerDict, layer)

    def _get_statsd_prometheus_exporter_pebble_config(self, _) -> ops.pebble.LayerDict:
        """Generate pebble config for the statsd-prometheus-exporter container.

        Returns:
            The pebble configuration for the container.
        """
        layer = {
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
        return typing.cast(ops.pebble.LayerDict, layer)

    def _get_installed_plugins(self, container: Container) -> List[str]:
        """Return plugins currently installed.

        Args:
            container: Container for which the installed plugins will be retrieved.

        Returns:
            List containing the installed plugins.
        """
        process = container.exec(["indico", "setup", "list-plugins"], user="indico")
        output, _ = process.wait_output()
        # Parse output table, discarding header and footer rows and fetching first column value
        return [item.split("|")[1].strip() for item in output.split("\n")[3:-2]]

    def _get_indico_secret_key_from_relation(self) -> Optional[str]:
        """Return the Indico secret key needed to deploy multiple Indico instances.

        Returns:
            Indico secret key.
        """
        peer_relation = self.model.get_relation("indico-peers")
        assert peer_relation is not None  # nosec
        if not self._has_secrets():
            secret_value = peer_relation.data[self.app].get("secret-key")
        else:
            secret_id = peer_relation.data[self.app].get("secret-id")
            if secret_id:
                secret = self.model.get_secret(id=secret_id)
                secret_value = secret.get_content().get("secret-key")
        return secret_value

    def _get_indico_env_config(self, container: Container) -> Dict:
        """Return an envConfig with some core configuration.

        Args:
            container: Container for which the configuration will be retrieved.

        Returns:
            Dictionary with the environment variables for the container.
        """
        available_plugins = self._get_installed_plugins(container)

        env_config = {
            "ATTACHMENT_STORAGE": "default",
            "CELERY_BROKER": self.redis_broker.url,
            "CE_ACCEPT_CONTENT": "json,pickle",
            "CUSTOMIZATION_DEBUG": self.config["customization_debug"],
            "ENABLE_ROOMBOOKING": self.config["enable_roombooking"],
            "INDICO_AUTH_PROVIDERS": str({}),
            "INDICO_DB_URI": self.database.uri,
            "INDICO_EXTRA_PLUGINS": ",".join(available_plugins),
            "INDICO_IDENTITY_PROVIDERS": str({}),
            "INDICO_NO_REPLY_EMAIL": self.config["indico_no_reply_email"],
            "INDICO_PUBLIC_SUPPORT_EMAIL": self.config["indico_public_support_email"],
            "INDICO_SUPPORT_EMAIL": self.config["indico_support_email"],
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "LC_LANG": "C.UTF-8",
            "REDIS_CACHE_URL": self.redis_cache.url,
            "SECRET_KEY": self._get_indico_secret_key_from_relation(),
            "SERVICE_HOSTNAME": self._get_external_hostname(),
            "SERVICE_PORT": self._get_external_port(),
            "SERVICE_SCHEME": self._get_external_scheme(),
            "STORAGE_DICT": {
                "default": "fs:/srv/indico/archive",
            },
        }

        if self.state.smtp_config:
            env_config["SMTP_LOGIN"] = self.state.smtp_config.login
            env_config["SMTP_PASSWORD"] = self.state.smtp_config.password
            env_config["SMTP_PORT"] = self.state.smtp_config.port
            env_config["SMTP_SERVER"] = self.state.smtp_config.host
            env_config["SMTP_USE_TLS"] = self.state.smtp_config.use_tls

        # Required for monitoring Celery
        celery_config = {"worker_send_task_events": True, "task_send_sent_event": True}
        env_config["CELERY_CONFIG"] = str(celery_config)

        # Piwik settings can't be configured using the config file for the time being:
        # https://github.com/indico/indico-plugins/issues/182
        if self.config["s3_storage"]:
            env_config["STORAGE_DICT"].update({"s3": self.config["s3_storage"]})  # type:ignore
            env_config["ATTACHMENT_STORAGE"] = "s3"
        env_config["STORAGE_DICT"] = str(env_config["STORAGE_DICT"])

        # SAML configuration reference https://github.com/onelogin/python3-saml
        if self.config["saml_target_url"]:
            saml_config = {}
            if self.config["saml_target_url"] == UBUNTU_SAML_URL:
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
                            "MIICjzCCAfigAwIBAgIJALNN/vxaR1hyMA0GCSqGSIb3DQEBBQUAMDoxCzAJBgNVBAYTA"
                            "kdCMRMwEQYDVQQIEwpTb21lLVN0YXRlMRYwFAYDVQQKEw1DYW5vbmljYWwgTHRkMB4XDT"
                            "EyMDgxMDEyNDE0OFoXDTEzMDgxMDEyNDE0OFowOjELMAkGA1UEBhMCR0IxEzARBgNVBAg"
                            "TClNvbWUtU3RhdGUxFjAUBgNVBAoTDUNhbm9uaWNhbCBMdGQwgZ8wDQYJKoZIhvcNAQEB"
                            "BQADgY0AMIGJAoGBAMM4pmIxkv419q8zj5EojK57y6plU/+k3apX6w1PgAYeI0zhNuud/"
                            "tiqKVQEDyZ6W7HNeGtWSh5rewy8c07BShcHG5Y8ibzBdIibGs5k6gvtmsRiXDE/F39+Rr"
                            "PSW18beHhEuoVJM9RANp3MYMOK11SiClSiGo+NfBKFuoqNX3UjAgMBAAGjgZwwgZkwHQY"
                            "DVR0OBBYEFH/no88pbywRnW6Fz+B4lQ04w/86MGoGA1UdIwRjMGGAFH/no88pbywRnW6F"
                            "z+B4lQ04w/86oT6kPDA6MQswCQYDVQQGEwJHQjETMBEGA1UECBMKU29tZS1TdGF0ZTEWM"
                            "BQGA1UEChMNQ2Fub25pY2FsIEx0ZIIJALNN/vxaR1hyMAwGA1UdEwQFMAMBAf8wDQYJKo"
                            "ZIhvcNAQEFBQADgYEArTGbZ1rg++aBxnNuJ7eho62JKKtRW5O+kMBvBLWi7fKck5uXDE6"
                            "d7Jv6hUy/gwUZV7r5kuPwRlw3Pu6AX4R60UsQuVG1/VVVI7nu32iCkXx5Vzq446IkVRdk"
                            "/QOda1dRyq0oaifUUhJfwVFSsm95ENDFdGqD0raj7g77ajcBMf8="
                        ),
                    },
                }
            elif self.config["saml_target_url"] == STAGING_UBUNTU_SAML_URL:
                saml_config = {
                    "strict": True,
                    "sp": {
                        "entityId": self.config["site_url"],
                    },
                    "idp": {
                        "entityId": "https://login.staging.ubuntu.com",
                        "singleSignOnService": {
                            "url": "https://login.staging.ubuntu.com/saml/",
                            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                        },
                        "singleLogoutService": {
                            "url": "https://login.staging.ubuntu.com/+logout",
                            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                        },
                        "x509cert": (
                            "MIIDuzCCAqOgAwIBAgIJALRwYFkmH3k9MA0GCSqGSIb3DQEBCwUAMHQxCzAJBgNVBAYTA"
                            "kdCMRMwEQYDVQQIDApTb21lLVN0YXRlMSswKQYDVQQKDCJTU08gU3RhZ2luZyBrZXkgZm"
                            "9yIEV4cGVuc2lmeSBTQU1MMSMwIQYDVQQDDBpTU08gU3RhZ2luZyBFeHBlbnNpZnkgU0F"
                            "NTDAeFw0xNTA5MjUxMDUzNTZaFw0xNjA5MjQxMDUzNTZaMHQxCzAJBgNVBAYTAkdCMRMw"
                            "EQYDVQQIDApTb21lLVN0YXRlMSswKQYDVQQKDCJTU08gU3RhZ2luZyBrZXkgZm9yIEV4c"
                            "GVuc2lmeSBTQU1MMSMwIQYDVQQDDBpTU08gU3RhZ2luZyBFeHBlbnNpZnkgU0FNTDCCAS"
                            "IwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBANyt2LqrD3DSmJMtNUA5xjJpbUNuiaH"
                            "FdO0AduOegfM7YnKIp0Y001S07ffEcv/zNo7Gg6wAZwLtW2/+eUkRj8PLEyYDyU2NiwD7"
                            "stAzhz50AjTbLojRyZdrEo6xu+f43xFNqf78Ix8mEKFr0ZRVVkkNRifa4niXPDdzIUiv5"
                            "UZUGjW0ybFKdM3zm6xjEwMwo8ixu/IbAn74PqC7nypllCvLjKLFeYmYN24oYaVKWIRhQu"
                            "GL3m98eQWFiVUL40palHtgcy5tffg8UOyAOqg5OF2kGVeyPZNmjq/jVHYyBUtBaMvrTLU"
                            "lOKRRC3I+aW9tXs7aqclQytOiFQxq+aEapB8CAwEAAaNQME4wHQYDVR0OBBYEFA9Ub7RI"
                            "fw21Qgbnf4IA3n4jUpAlMB8GA1UdIwQYMBaAFA9Ub7RIfw21Qgbnf4IA3n4jUpAlMAwGA"
                            "1UdEwQFMAMBAf8wDQYJKoZIhvcNAQELBQADggEBAGBHECvs8V3xBKGRvNfBaTbY2FpbwL"
                            "heSm3MUM4/hswvje24oknoHMF3dFNVnosOLXYdaRf8s0rsJfYuoUTap9tKzv0osGoA3mM"
                            "w18LYW3a+mUHurx+kJZP+VN3emk84TXiX44CCendMVMxHxDQwg40YxALNc4uew2hlLReB"
                            "8nC+55OlsIInIqPcIvtqUZgeNp2iecKnCgZPDaElez52GY5GRFszJd04sAQIrpg2+xfZv"
                            "LMtvWwb9rpdto5oIdat2gIoMLdrmJUAYWP2+BLiKVpe9RtzfvqtQrk1lDoTj3adJYutNI"
                            "PbTGOfI/Vux0HCw9KCrNTspdsfGTIQFJJi01E="
                        ),
                    },
                }
            auth_providers = {"ubuntu": {"type": "saml", "saml_config": saml_config}}
            env_config["INDICO_AUTH_PROVIDERS"] = str(auth_providers)
            identity_providers = {
                "ubuntu": {
                    "type": (
                        "saml_groups" if SAML_GROUPS_PLUGIN_NAME in available_plugins else "saml"
                    ),
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
            env_config = {
                **env_config,
                **self._get_http_proxy_configuration(self.state.proxy_config),
            }
        return env_config

    def _get_indico_env_config_str(self, container: Container) -> Dict[str, str]:
        """Get indico environment config.

        Args:
            container: Indico container that has the target environment configuration.

        Returns:
            Indico environment config.
        """
        indico_env_config = self._get_indico_env_config(container)
        return {env_name: str(value) for env_name, value in indico_env_config.items()}

    def _get_http_proxy_configuration(self, proxy: Optional[ProxyConfig] = None) -> Dict[str, str]:
        """Generate http proxy config.

        Args:
            proxy: Proxy configuration.

        Returns:
            Map containing the HTTP_PROXY environment variables.
        """
        if proxy:
            return {
                "HTTP_PROXY": str(proxy.http_proxy),
                "HTTPS_PROXY": str(proxy.https_proxy),
                "NO_PROXY": str(proxy.no_proxy),
            }
        return {}

    def _is_saml_target_url_valid(self) -> bool:
        """Check if the target SAML URL is currently supported.

        Returns:
            If the SAML config is valid or not.
        """
        return (
            not self.config["saml_target_url"]
            or UBUNTU_SAML_URL == self.config["saml_target_url"]
            or STAGING_UBUNTU_SAML_URL == self.config["saml_target_url"]
        )

    def _on_config_changed(self, event: HookEvent) -> None:
        """Handle changes in configuration.

        Args:
            event: Event triggering the configuration change handler.
        """
        if not self._are_relations_ready(event):
            return
        if not self._is_saml_target_url_valid():
            self.unit.status = BlockedStatus(
                "Invalid saml_target_url option provided. "
                f"Only {UBUNTU_SAML_URL} and {STAGING_UBUNTU_SAML_URL} are available."
            )
            return
        if not self._are_pebble_instances_ready():
            self.unit.status = WaitingStatus("Waiting for pebble")
            return
        self.model.unit.status = MaintenanceStatus("Configuring pod")
        is_valid, error = self._is_configuration_valid()
        if not is_valid:
            self.model.unit.status = BlockedStatus(error)
            return
        for container_name in self.model.unit.containers:
            self._config_pebble(self.unit.get_container(container_name))

    def _get_current_customization_url(self) -> str:
        """Get the current remote repository for the customization changes.

        Returns:
            The customization URL.
        """
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
        return remote_url.rstrip()

    def _install_plugins(self, container: Container, plugins: List[str]) -> None:
        """Install the external plugins.

        Args:
            container: Container where the plugins will be installed.
            plugins: List of plugins to be installed.
        """
        if plugins:
            process = container.exec(
                ["pip", "install", "--upgrade"] + plugins,
                environment=self._get_http_proxy_configuration(self.state.proxy_config),
            )
            process.wait_output()

    def _get_indico_version(self) -> str:
        """Retrieve the current version of Indico.

        Returns:
            The indico version installed.
        """
        container = self.unit.get_container("indico")
        process = container.exec(["indico", "--version"], user="indico")
        version_string, _ = process.wait_output()
        version = findall("[0-9.]+", version_string)
        return version[0] if version else ""

    def _exec_cmd_in_custom_dir(self, container: Container, command: List[str]) -> None:
        """Execute command in indico customization directory.

        Args:
            container: Container in which the command will be executed.
            command: command to execute. The first item is the name (or path)
                    of the executable, the rest of the items are the arguments.
        """
        process = container.exec(
            command,
            working_dir=INDICO_CUSTOMIZATION_DIR,
            user="indico",
            environment=self._get_http_proxy_configuration(self.state.proxy_config),
        )
        process.wait_output()

    def _download_customization_changes(self, container: Container) -> None:
        """Clone the remote repository with the customization changes.

        Args:
            container: Container in which the download will be performed.
        """
        current_remote_url = self._get_current_customization_url()
        if current_remote_url != self.config["customization_sources_url"]:
            logging.debug(
                "Removing old contents from directory %s. Previous repository: '%s'",
                INDICO_CUSTOMIZATION_DIR,
                current_remote_url,
            )
            process = container.exec(["rm", "-rf", INDICO_CUSTOMIZATION_DIR], user="indico")
            process.wait_output()
            process = container.exec(["mkdir", INDICO_CUSTOMIZATION_DIR], user="indico")
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
        """Pull changes from the remote repository and upgrade external plugins.

        Returns:
            Dictionary containing the execution results for each of the operations executed.
        """
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
        """Refresh external resources and report action result.

        Args:
            event: Event triggering the refresh action.
        """
        results = self._refresh_external_resources(event)
        event.set_results(results)

    def _on_leader_elected(self, _) -> None:
        """Handle leader-elected event."""
        peer_relation = self.model.get_relation("indico-peers")
        secret_value = repr(os.urandom(32))
        if (
            peer_relation
            and not self._has_secrets()
            and not peer_relation.data[self.app].get("secret-key")
        ):
            peer_relation.data[self.app].update({"secret-key": secret_value})
        elif (
            peer_relation
            and self._has_secrets()
            and not peer_relation.data[self.app].get("secret-id")
        ):
            secret = self.app.add_secret({"secret-key": secret_value})
            peer_relation.data[self.app].update({"secret-id": secret.id})

    def _has_secrets(self) -> bool:
        """Check if current Juju version supports secrets.

        Returns:
            If secrets are supported or not.
        """
        juju_version = JujuVersion.from_environ()
        # Because we're only using secrets in a peer relation we don't need to
        # check if the other end of a relation also supports secrets...
        return juju_version.has_secrets

    def _add_admin_action(self, event: ActionEvent) -> None:
        """Add a new user to Indico.

        Args:
            event: Event triggered by the add_admin action
        """
        container = self.unit.get_container("indico")
        indico_env_config = self._get_indico_env_config_str(container)

        cmd = [
            "/usr/local/bin/indico",
            "autocreate",
            "admin",
            event.params["email"],
            event.params["password"],
        ]

        if container.can_connect():
            process = container.exec(
                cmd,
                user="indico",
                working_dir="/srv/indico",
                environment=indico_env_config,
            )
            try:
                output = process.wait_output()
                event.set_results({"user": f"{event.params['email']}", "output": output})
            except ExecError as ex:
                logger.exception("Action add-admin failed: %s", ex.stdout)

                event.fail(
                    # Parameter validation errors are printed to stdout
                    f"Failed to create admin {event.params['email']}: {ex.stdout!r}"
                )

    def _execute_anonymize_cmd(self, event: ActionEvent) -> Iterator[str]:
        """Execute anonymize command for each email.

        Args:
            event (ActionEvent): Event triggered by the anonymize-user action

        Yields:
            Iterator[str]: Output of each command execution
        """
        container = self.unit.get_container("indico")
        indico_env_config = self._get_indico_env_config_str(container)
        for email in event.params["email"].split(EMAIL_LIST_SEPARATOR):
            cmd = [
                "/usr/local/bin/indico",
                "anonymize",
                "user",
                email,
            ]

            if not container.can_connect():
                logger.error(
                    "Action anonymize-user failed: cannot connect to the Indico workload container"
                )
                self.unit.status = WaitingStatus(
                    "Waiting to be able to connect to workload container"
                )
                return

            process = container.exec(
                cmd,
                user="indico",
                working_dir="/srv/indico",
                environment=indico_env_config,
            )
            try:
                out = process.wait_output()
                yield out[0].replace("\n", "")
            except ExecError as ex:
                logger.exception("Action anonymize-user failed: %s", ex.stdout)
                fail_msg = f"Failed to anonymize user {event.params['email']}: {ex.stdout!r}"
                event.fail("Failed to anonymize one or more users, please verify the results.")
                yield fail_msg

    def _anonymize_user_action(self, event: ActionEvent) -> None:
        """Anonymize user in Indico.

        If find an error, the action will fail. All the results will be set until the error
        has happened.

        Args:
            event: Event triggered by the anonymize-user action
        """
        if len(event.params["email"].split(EMAIL_LIST_SEPARATOR)) > EMAIL_LIST_MAX:
            max_reached_msg = (
                "Failed to anonymize user: "
                f"List of more than {EMAIL_LIST_MAX} emails are not allowed"
            )
            logger.error("Action anonymize-user failed: %s", max_reached_msg)
            event.fail(max_reached_msg)
            return
        output_list = list(self._execute_anonymize_cmd(event))
        event.set_results(
            {
                "user": f"{event.params['email']}",
                "output": EMAIL_LIST_SEPARATOR.join(output_list),
            }
        )


if __name__ == "__main__":  # pragma: no cover
    main(IndicoOperatorCharm, use_juju_for_storage=True)
