#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Charm for Indico on kubernetes."""
import logging
import os
import typing
from re import findall
from typing import Any, Dict, Iterator, List, Optional, Tuple
from urllib.parse import urlparse

import charms.loki_k8s.v0.loki_push_api
import ops
from charms.grafana_k8s.v0.grafana_dashboard import GrafanaDashboardProvider
from charms.loki_k8s.v0.loki_push_api import LogProxyConsumer
from charms.nginx_ingress_integrator.v0.nginx_route import require_nginx_route
from charms.prometheus_k8s.v0.prometheus_scrape import MetricsEndpointProvider
from charms.redis_k8s.v0.redis import RedisRelationCharmEvents, RedisRequires
from ops.charm import ActionEvent, CharmBase, HookEvent, PebbleReadyEvent, RelationDepartedEvent
from ops.jujuversion import JujuVersion
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus, Container, MaintenanceStatus, WaitingStatus
from ops.pebble import ExecError

from database_observer import DatabaseObserver
from s3_observer import S3Observer
from saml_observer import SamlObserver
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
SAML_GROUPS_PLUGIN_NAME = "saml_groups"

UWSGI_TOUCH_RELOAD = "/srv/indico/indico.wsgi"


class InvalidRedisNameError(Exception):
    """Represents invalid redis name error."""


class IndicoOperatorCharm(CharmBase):  # pylint: disable=too-many-instance-attributes
    """Charm for Indico on kubernetes.

    Attrs:
        on: Redis relation charm events.
    """

    on = RedisRelationCharmEvents()

    def __init__(self, *args):
        """Construct.

        Args:
            args: Arguments passed to the CharmBase parent constructor.
        """
        super().__init__(*args)
        self.database = DatabaseObserver(self)
        self.s3 = S3Observer(self)
        self.smtp = SmtpObserver(self)
        self.saml = SamlObserver(self)
        try:
            self.state = State.from_charm(
                self,
                s3_relation_data=self.s3.s3.get_s3_connection_info(),
                smtp_relation_data=self.smtp.smtp.get_relation_data(),
                saml_relation_data=self.saml.saml.get_relation_data(),
            )
        except CharmConfigInvalidError as exc:
            self.unit.status = ops.BlockedStatus(exc.msg)
            return
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.leader_elected, self._on_leader_elected)
        self.framework.observe(self.on.indico_pebble_ready, self._on_pebble_ready)
        self.framework.observe(self.on.indico_nginx_pebble_ready, self._on_pebble_ready)
        self.framework.observe(
            self.on.refresh_external_resources_action, self._refresh_external_resources_action
        )
        # self.framework.observe(self.on.update_status, self._refresh_external_resources)
        self.framework.observe(self.on.add_admin_action, self._add_admin_action)
        self.framework.observe(self.on.anonymize_user_action, self._anonymize_user_action)
        self.redis_broker = RedisRequires(self, "redis-broker")
        self.framework.observe(
            self.redis_broker.charm.on.redis_relation_updated, self._on_config_changed
        )
        self.redis_cache = RedisRequires(self, "redis-cache")
        self.framework.observe(
            self.redis_cache.charm.on.redis_relation_updated, self._on_config_changed
        )
        self.framework.observe(
            self.on["indico-peers"].relation_departed, self._on_peer_relation_departed
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
        # port 9080 conflicts with the nginx exporter
        charms.loki_k8s.v0.loki_push_api.HTTP_LISTEN_PORT = 9090
        self._logging = LogProxyConsumer(
            self,
            relation_name="logging",
            log_files="/srv/indico/log/*",
            container_name="indico",
        )

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
        site_url = typing.cast(str, self.config["site_url"])
        if site_url and not urlparse(site_url).hostname:
            return False, "Configuration option site_url is not valid"
        return True, ""

    def _get_external_hostname(self) -> str:
        """Extract and return hostname from site_url or default to [application name].local.

        Returns:
            The site URL defined as part of the site_url configuration or a default value.
        """
        site_url = typing.cast(str, self.config["site_url"])
        if not site_url or not (hostname := urlparse(site_url).hostname):
            return f"{self.app.name}.local"
        return hostname

    def _get_external_scheme(self) -> str:
        """Extract and return schema from site_url.

        Returns:
            The HTTP schema.
        """
        site_url = typing.cast(str, self.config["site_url"])
        return urlparse(site_url).scheme if site_url else "http"

    def _get_external_port(self) -> Optional[int]:
        """Extract and return port from site_url.

        Returns:
            The port number.
        """
        site_url = typing.cast(str, self.config["site_url"])
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
        if container.name == "indico":
            # Plugins need to be installed before adding the layer so that
            # they are included in the corresponding env vars
            plugins = (
                typing.cast(str, self.config["external_plugins"]).split(",")
                if self.config["external_plugins"]
                else []
            )
            self._install_plugins(container, plugins)
            container.add_layer(container.name, self._get_logrotate_config(), combine=True)
            indico_config = self._get_indico_pebble_config(container)
            container.add_layer(container.name, indico_config, combine=True)
            peer_relation = self.model.get_relation("indico-peers")
            if (
                not peer_relation
                or peer_relation.data[self.app].get("celery-unit") == self.unit.name
            ):
                celery_config = self._get_celery_pebble_config(container)
                container.add_layer("celery", celery_config, combine=True)
                celery_exporter_config = self._get_celery_prometheus_exporter_pebble_config(
                    container
                )
                container.add_layer("celery-exporter", celery_exporter_config, combine=True)
            statsd_config = self._get_statsd_prometheus_exporter_pebble_config(container)
            container.add_layer("statsd", statsd_config, combine=True)
            self._download_customization_changes(container)
        if container.name == "indico-nginx":
            nginx_config = self._get_nginx_pebble_config(container)
            container.add_layer(container.name, nginx_config, combine=True)
            nginx_exporter_config = self._get_nginx_prometheus_exporter_pebble_config(container)
            container.add_layer("nginx", nginx_exporter_config, combine=True)
        self.unit.status = MaintenanceStatus(f"Starting {container.name} container")
        container.pebble.replan_services()
        if self._are_pebble_instances_ready():
            self.unit.set_workload_version(self._get_indico_version())
            self.unit.status = ActiveStatus()
        else:
            self.unit.status = WaitingStatus("Waiting for pebble")

    def _get_logrotate_config(self) -> ops.pebble.LayerDict:
        """Generate logrotate pebble layer.

        Returns:
            The logrotate pebble layer configuration.
        """
        layer = {
            "summary": "Logrotate service",
            "description": "Logrotate service",
            "services": {
                "logrotate": {
                    "override": "replace",
                    "command": 'bash -c "while :; '
                    "do sleep 3600; logrotate /srv/indico/logrotate.conf; "
                    'done"',
                    "startup": "enabled",
                },
            },
        }
        return typing.cast(ops.pebble.LayerDict, layer)

    def _get_indico_pebble_config(self, container: Container) -> ops.pebble.LayerDict:
        """Generate pebble config for the indico container.

        Args:
            container: Indico container that has the target configuration.

        Returns:
            The pebble configuration for the container.
        """
        indico_env_config = self._get_indico_env_config(container)
        indico_env_config["INDICO_LOGGING_CONFIG_FILE"] = "indico.logging.yaml"
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

    def _get_celery_pebble_config(self, container: Container) -> ops.pebble.LayerDict:
        """Generate pebble config for the celery container.

        Args:
            container: Celery container that has the target configuration.

        Returns:
            The pebble configuration for the container.
        """
        indico_env_config = self._get_indico_env_config(container)
        indico_env_config["INDICO_LOGGING_CONFIG_FILE"] = "celery.logging.yaml"
        layer = {
            "summary": "Indico celery layer",
            "description": "Indico celery layer",
            "services": {
                "celery": {
                    "override": "replace",
                    "summary": "Indico celery",
                    "command": "/usr/bin/indico celery worker -B -E",
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
                        "command": "/usr/bin/indico celery inspect ping",
                        "environment": indico_env_config,
                    },
                },
            },
        }
        return typing.cast(ops.pebble.LayerDict, layer)

    def _get_nginx_pebble_config(self, _) -> ops.pebble.LayerDict:
        """Generate pebble config for the indico-nginx container.

        Returns:
            The pebble configuration for the container.
        """
        layer = {
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
        return typing.cast(ops.pebble.LayerDict, layer)

    def _get_redis_url(self, redis_name: str) -> Optional[str]:
        """Get Url for redis charm.

        Args:
            redis_name (str): Name of the redis charm to connect to.

        Returns:
            Url for the redis charm.

        Raises:
           InvalidRedisNameError: If redis name is invalid
        """
        if redis_name == "redis-broker":
            redis = self.redis_broker
        elif redis_name == "redis-cache":
            redis = self.redis_cache
        else:
            raise InvalidRedisNameError(f"Invalid Redis name: {redis_name}")

        relation = self.model.get_relation(redis.relation_name)
        if not relation:
            return None
        relation_app_data = relation.data[relation.app]
        relation_unit_data = redis.relation_data

        try:
            redis_hostname = str(
                relation_app_data.get("leader-host", relation_unit_data["hostname"])
            )
            redis_port = int(relation_unit_data["port"])
            return f"redis://{redis_hostname}:{redis_port}"
        except KeyError:
            return None
        return None

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
                        f" --broker-url={self._get_redis_url('redis-broker')}"
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
            "CELERY_BROKER": self._get_redis_url("redis-broker"),
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
            "REDIS_CACHE_URL": self._get_redis_url("redis-cache"),
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
        # S3 available config options:
        # https://github.com/indico/indico-plugins/blob/master/storage_s3/README.md#available-config-options
        if self.state.s3_config:
            env_config["STORAGE_DICT"].update({"s3": self.state.s3_config.get_connection_string()})
            env_config["ATTACHMENT_STORAGE"] = "s3"
        env_config["STORAGE_DICT"] = str(env_config["STORAGE_DICT"])

        # SAML configuration reference https://github.com/onelogin/python3-saml
        if self.state.saml_config:
            saml_config: Dict[str, Any] = {
                "strict": True,
                "sp": {
                    "entityId": self.config["site_url"],
                },
                "idp": {
                    "entityId": self.state.saml_config.entity_id,
                    "x509cert": self.state.saml_config.certificates[0],
                },
            }
            for endpoint in self.state.saml_config.endpoints:
                # First letter needs to be lowercase
                endpoint_name = endpoint.name[:1].lower() + endpoint.name[1:]
                saml_config["idp"][endpoint_name] = {
                    "url": str(endpoint.url),
                    "binding": endpoint.binding,
                }
                if endpoint.response_url:
                    saml_config["idp"][endpoint_name]["response_url"] = str(endpoint.response_url)
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

    def _on_config_changed(self, event: HookEvent) -> None:
        """Handle changes in configuration.

        Args:
            event: Event triggering the configuration change handler.
        """
        if not self._are_relations_ready(event):
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
            install_command = ["pip", "install", "--upgrade"] + plugins
            logger.info("About to run: %s", " ".join(install_command))
            process = container.exec(
                install_command,
                environment=self._get_http_proxy_configuration(self.state.proxy_config),
            )
            output, _ = process.wait_output()
            logger.info("Output was: %s", output)

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
                    container,
                    [
                        "git",
                        "clone",
                        typing.cast(str, self.config["customization_sources_url"]),
                        ".",
                    ],
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
                plugins = typing.cast(str, self.config["external_plugins"]).split(",")
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
            peer_relation.data[self.app].update({"secret-id": typing.cast(str, secret.id)})
        if peer_relation and not peer_relation.data[self.app].get("celery-unit"):
            peer_relation.data[self.app].update({"celery-unit": self.unit.name})

    def _on_peer_relation_departed(self, event: RelationDepartedEvent) -> None:
        """Handle the peer relation departed event.

        Args:
            event: the event triggering the handler.
        """
        peer_relation = self.model.get_relation("indico-peers")
        if (
            self.unit.is_leader()
            and peer_relation
            and event.departing_unit
            and peer_relation.data[self.app].get("celery-unit") == event.departing_unit.name
        ):
            if self.unit != event.departing_unit:
                peer_relation.data[self.app].update({"celery-unit": self.unit.name})
                container = self.unit.get_container("indico")
                if self._are_relations_ready(event) and container.can_connect():
                    self._config_pebble(container)
            else:
                # Leadership election will select a new celery-unit
                peer_relation.data[self.app].update({"celery-unit": ""})

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
            "/usr/bin/indico",
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
                "/usr/bin/indico",
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
