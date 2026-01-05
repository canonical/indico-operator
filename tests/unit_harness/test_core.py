# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Indico charm unit tests."""

# pylint:disable=duplicate-code,protected-access
from ast import literal_eval
from secrets import token_hex
from unittest.mock import MagicMock, patch

import ops
import pytest
from ops.testing import Harness

from charm import IndicoOperatorCharm
from state import S3Config, SamlConfig, SamlEndpoint, SmtpConfig
from tests.unit_harness.test_base import TestBase


def test_proxyconfig_invalid(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched os.environ mapping that contains invalid proxy values.
    act: when charm is initialized.
    assert: the charm reaches blocked status.
    """
    monkeypatch.setenv("JUJU_CHARM_HTTP_PROXY", "INVALID_URL")
    harness = Harness(IndicoOperatorCharm)
    harness.begin()
    assert harness.model.unit.status.name == ops.BlockedStatus().name


class TestCore(TestBase):  # pylint: disable=too-many-public-methods
    """Indico charm unit tests."""

    def test_redis_ha(self):
        """
        arrange: charm created
        act: change leader-host
        assert: the charm gets the changed url
        """
        self.setUp()
        broker_host = "broker-host"
        broker_port = "1010"
        cache_host = "cache-host"
        cache_port = "1011"

        redis_broker_relation_id = self.harness.add_relation(
            "redis-broker",
            "redis-broker",
            unit_data={"hostname": broker_host, "port": broker_port},
            app_data={"leader-host": broker_host},
        )
        self.harness.add_relation_unit(redis_broker_relation_id, "redis-broker/1")
        self.harness.update_relation_data(
            redis_broker_relation_id,
            "redis-broker/1",
            {"hostname": "broker-host-1", "port": broker_port},
        )
        redis_cache_relation_id = self.harness.add_relation(
            "redis-cache",
            "redis-cache",
            unit_data={"hostname": cache_host, "port": cache_port},
            app_data={"leader-host": cache_host},
        )
        self.harness.add_relation_unit(redis_cache_relation_id, "redis-cache/1")
        self.harness.update_relation_data(
            redis_cache_relation_id,
            "redis-cache/1",
            {"hostname": "cache-host-1", "port": cache_port},
        )

        broker_url = self.harness.charm._get_redis_url("redis-broker")
        cache_url = self.harness.charm._get_redis_url("redis-cache")
        self.assertEqual(broker_url, f"redis://{broker_host}:{broker_port}")
        self.assertEqual(cache_url, f"redis://{cache_host}:{cache_port}")
        broker_host = "broker-host-1"
        cache_host = "cache-host-1"

        self.harness.update_relation_data(
            redis_broker_relation_id,
            "redis-broker",
            {"leader-host": broker_host},
        )

        self.harness.update_relation_data(
            redis_cache_relation_id,
            "redis-cache",
            {"leader-host": cache_host},
        )
        broker_url = self.harness.charm._get_redis_url("redis-broker")
        cache_url = self.harness.charm._get_redis_url("redis-cache")
        self.assertEqual(broker_url, f"redis://{broker_host}:{broker_port}")
        self.assertEqual(cache_url, f"redis://{cache_host}:{cache_port}")

    def test_redis_ha_old(self):
        """
        arrange: charm created
        act: add redis relation with old redis databag
        assert: the charm gets the correct url
        """
        self.setUp()
        broker_host = "broker-host"
        broker_port = "1010"
        cache_host = "cache-host"
        cache_port = "1011"

        self.harness.add_relation(
            "redis-broker",
            "redis-broker",
            unit_data={"hostname": broker_host, "port": broker_port},
        )

        self.harness.add_relation(
            "redis-cache",
            "redis-cache",
            unit_data={"hostname": cache_host, "port": cache_port},
        )
        broker_url = self.harness.charm._get_redis_url("redis-broker")
        cache_url = self.harness.charm._get_redis_url("redis-cache")
        self.assertEqual(broker_url, f"redis://{broker_host}:{broker_port}")
        self.assertEqual(cache_url, f"redis://{cache_host}:{cache_port}")

    def test_missing_relations(self):
        """
        arrange: charm created
        act: trigger a configuration update
        assert: the charm is in waiting status until all relations have been set
        """
        self.harness.update_config({"site_url": "foo"})
        self.assertEqual(
            self.harness.model.unit.status,
            ops.WaitingStatus("Waiting for redis-broker availability"),
        )
        self.harness.add_relation(
            "redis-broker",
            "redis-broker",
            unit_data={"something": "just to trigger rel-changed event"},
        )
        self.assertEqual(
            self.harness.model.unit.status,
            ops.WaitingStatus("Waiting for redis-cache availability"),
        )
        self.harness.add_relation(
            "redis-cache",
            "redis-cache",
            unit_data={"something": "just to trigger rel-changed event"},
        )
        self.assertEqual(
            self.harness.model.unit.status, ops.WaitingStatus("Waiting for database availability")
        )

    @patch.object(ops.Container, "exec")
    def test_indico_nginx_pebble_ready(self, mock_exec):
        """
        arrange: charm created
        act: trigger container pebble ready event for nginx container
        assert: the container and the service are running
        """
        mock_exec.return_value = MagicMock(wait_output=MagicMock(return_value=("", None)))

        self.set_up_all_relations()
        self.harness.set_leader(True)

        self.harness.container_pebble_ready("indico-nginx")

        service = self.harness.model.unit.get_container("indico-nginx").get_service("indico-nginx")
        self.assertTrue(service.is_running())
        self.assertEqual(self.harness.model.unit.status, ops.WaitingStatus("Waiting for pebble"))

    @patch.object(ops.Container, "exec")
    def test_all_pebble_services_ready(self, mock_exec):
        """
        arrange: charm created and relations established
        act: trigger container pebble ready event for all containers
        assert: the containers and the services are running and the charm reaches active status
        """
        mock_exec.return_value = MagicMock(wait_output=MagicMock(return_value=("", None)))

        self.set_up_all_relations()
        self.harness.set_leader(True)

        self.harness.container_pebble_ready("indico")
        self.assertEqual(self.harness.model.unit.status, ops.WaitingStatus("Waiting for pebble"))
        self.harness.container_pebble_ready("indico-nginx")
        self.assertEqual(self.harness.model.unit.status, ops.ActiveStatus())

    @patch.object(ops.JujuVersion, "from_environ")
    @patch.object(ops.Container, "exec")
    def test_indico_pebble_ready_when_secrets_not_enabled(self, mock_exec, mock_juju_env):
        """
        arrange: charm created, secrets not supported and relations established
        act: trigger container pebble ready event for the Indico container
        assert: the container and the service are running and properly configured
        """
        mock_juju_env.return_value = MagicMock(has_secrets=False)
        mock_exec.return_value = MagicMock(wait_output=MagicMock(return_value=("", None)))
        self.set_up_all_relations()
        self.harness.set_leader(True)

        self.harness.container_pebble_ready("indico")

        updated_plan = self.harness.get_container_pebble_plan("indico").to_dict()
        updated_plan_env = updated_plan["services"]["indico"]["environment"]
        self.assertEqual(
            "postgresql://user1:somepass@postgresql-k8s-primary.local:5432/indico",
            updated_plan_env["INDICO_DB_URI"],
        )
        self.assertEqual("redis://broker-host:1010", updated_plan_env["CELERY_BROKER"])
        peer_relation = self.harness.model.get_relation("indico-peers")
        self.assertEqual(
            self.harness.get_relation_data(peer_relation.id, self.harness.charm.app.name).get(
                "secret-key"
            ),
            updated_plan_env["SECRET_KEY"],
        )
        self.assertEqual("indico.local", updated_plan_env["SERVICE_HOSTNAME"])
        self.assertIsNone(updated_plan_env["SERVICE_PORT"])
        self.assertEqual("redis://cache-host:1011", updated_plan_env["REDIS_CACHE_URL"])
        self.assertFalse(updated_plan_env["ENABLE_ROOMBOOKING"])
        self.assertEqual("support-tech@mydomain.local", updated_plan_env["INDICO_SUPPORT_EMAIL"])
        self.assertEqual("support@mydomain.local", updated_plan_env["INDICO_PUBLIC_SUPPORT_EMAIL"])
        self.assertEqual("noreply@mydomain.local", updated_plan_env["INDICO_NO_REPLY_EMAIL"])
        self.assertFalse(updated_plan_env["CUSTOMIZATION_DEBUG"])
        self.assertEqual("default", updated_plan_env["ATTACHMENT_STORAGE"])
        storage_dict = literal_eval(updated_plan_env["STORAGE_DICT"])
        self.assertEqual("fs:/srv/indico/archive", storage_dict["default"])

        service = self.harness.model.unit.get_container("indico").get_service("indico")
        self.assertTrue(service.is_running())
        self.assertEqual(self.harness.model.unit.status, ops.WaitingStatus("Waiting for pebble"))

    @patch.object(ops.JujuVersion, "from_environ")
    @patch.object(ops.Container, "exec")
    def test_indico_pebble_ready_when_secrets_enabled(self, mock_exec, mock_juju_env):
        """
        arrange: charm created, secrets supported and relations established
        act: trigger container pebble ready event for the Indico container
        assert: the container and the service are running and properly configured
        """
        mock_juju_env.return_value = MagicMock(has_secrets=True)
        mock_exec.return_value = MagicMock(wait_output=MagicMock(return_value=("", None)))
        self.set_up_all_relations()
        self.harness.set_leader(True)
        smtp_config = SmtpConfig(
            host="localhost",
            port=8025,
            login="user",
            password=token_hex(16),
            use_tls=False,
        )
        self.harness.charm.state.smtp_config = smtp_config
        self.harness.container_pebble_ready("indico")

        updated_plan = self.harness.get_container_pebble_plan("indico").to_dict()
        updated_plan_env = updated_plan["services"]["indico"]["environment"]
        self.assertEqual(
            "postgresql://user1:somepass@postgresql-k8s-primary.local:5432/indico",
            updated_plan_env["INDICO_DB_URI"],
        )
        self.assertEqual("redis://broker-host:1010", updated_plan_env["CELERY_BROKER"])
        peer_relation = self.harness.model.get_relation("indico-peers")
        secret_id = self.harness.get_relation_data(
            peer_relation.id, self.harness.charm.app.name
        ).get("secret-id")
        secret = self.harness.model.get_secret(id=secret_id)
        secret_value = secret.get_content().get("secret-key")
        self.assertEqual(secret_value, updated_plan_env["SECRET_KEY"])
        self.assertEqual("indico.local", updated_plan_env["SERVICE_HOSTNAME"])
        self.assertIsNone(updated_plan_env["SERVICE_PORT"])
        self.assertEqual("redis://cache-host:1011", updated_plan_env["REDIS_CACHE_URL"])
        self.assertFalse(updated_plan_env["ENABLE_ROOMBOOKING"])
        self.assertEqual("support-tech@mydomain.local", updated_plan_env["INDICO_SUPPORT_EMAIL"])
        self.assertEqual("support@mydomain.local", updated_plan_env["INDICO_PUBLIC_SUPPORT_EMAIL"])
        self.assertEqual("noreply@mydomain.local", updated_plan_env["INDICO_NO_REPLY_EMAIL"])
        self.assertFalse(updated_plan_env["CUSTOMIZATION_DEBUG"])
        self.assertEqual("default", updated_plan_env["ATTACHMENT_STORAGE"])
        storage_dict = literal_eval(updated_plan_env["STORAGE_DICT"])
        self.assertEqual("fs:/srv/indico/archive", storage_dict["default"])
        self.assertEqual(smtp_config.host, updated_plan_env["SMTP_SERVER"])
        self.assertEqual(smtp_config.port, updated_plan_env["SMTP_PORT"])
        self.assertEqual(smtp_config.login, updated_plan_env["SMTP_LOGIN"])
        self.assertEqual(smtp_config.password, updated_plan_env["SMTP_PASSWORD"])
        self.assertFalse(updated_plan_env["SMTP_USE_TLS"])

        service = self.harness.model.unit.get_container("indico").get_service("indico")
        self.assertTrue(service.is_running())
        service = self.harness.model.unit.get_container("indico").get_service("celery")
        self.assertTrue(service.is_running())
        self.assertEqual(self.harness.model.unit.status, ops.WaitingStatus("Waiting for pebble"))

    @patch.object(ops.Container, "exec")
    @patch("charm.secrets")
    def test_config_changed(self, mock_secrets, mock_exec):  # pylint: disable=R0915
        """
        arrange: charm created and relations established
        act: trigger a valid configuration change for the charm
        assert: the container and the service are running and properly configured
        """
        mock_exec.return_value = MagicMock(wait_output=MagicMock(return_value=("", None)))
        mock_secrets.token_hex.return_value = "123456"

        self.set_relations_and_leader()
        saml_endpoints = (
            SamlEndpoint(
                name="SingleSignOnService",
                url="https://example.com/login",
                binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            ),
            SamlEndpoint(
                name="SingleLogoutService",
                url="https://example.com/logout",
                binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                response_url="https://example.com/response",
            ),
        )
        saml_config = SamlConfig(
            entity_id="entity",
            metadata_url="https://example.com/metadata",
            certificates=("cert1,", "cert2"),
            endpoints=saml_endpoints,
        )
        s3_config = S3Config(
            bucket="test-bucket",
            host="s3.example.com",
            access_key=token_hex(16),
            secret_key=token_hex(16),
        )
        self.harness.charm.state.s3_config = s3_config
        self.harness.charm.state.saml_config = saml_config
        self.harness.update_config(
            {
                "customization_debug": True,
                "customization_sources_url": "https://example.com/custom",
                "enable_roombooking": True,
                "external_plugins": "git+https://example.git/#subdirectory=themes_cern",
                "indico_support_email": "example@email.local",
                "indico_public_support_email": "public@email.local",
                "indico_no_reply_email": "noreply@email.local",
                "site_url": "https://example.local:8080",
            }
        )

        updated_plan = self.harness.get_container_pebble_plan("indico").to_dict()
        updated_plan_env = updated_plan["services"]["indico"]["environment"]

        self.assertEqual("example.local", updated_plan_env["SERVICE_HOSTNAME"])
        self.assertTrue(updated_plan_env["ENABLE_ROOMBOOKING"])
        self.assertEqual("example@email.local", updated_plan_env["INDICO_SUPPORT_EMAIL"])
        self.assertEqual("public@email.local", updated_plan_env["INDICO_PUBLIC_SUPPORT_EMAIL"])
        self.assertEqual("noreply@email.local", updated_plan_env["INDICO_NO_REPLY_EMAIL"])
        self.assertEqual("https", updated_plan_env["SERVICE_SCHEME"])
        self.assertEqual(8080, updated_plan_env["SERVICE_PORT"])
        self.assertTrue(updated_plan_env["CUSTOMIZATION_DEBUG"])
        storage_dict = literal_eval(updated_plan_env["STORAGE_DICT"])
        self.assertEqual("s3", updated_plan_env["ATTACHMENT_STORAGE"])
        self.assertEqual("fs:/srv/indico/archive", storage_dict["default"])
        self.assertEqual(
            (
                f"s3:bucket={s3_config.bucket},access_key={s3_config.access_key},"
                f"secret_key={s3_config.secret_key},proxy=true,host={s3_config.host}"
            ),
            storage_dict["s3"],
        )
        auth_providers = literal_eval(updated_plan_env["INDICO_AUTH_PROVIDERS"])
        self.assertEqual("saml", auth_providers["ubuntu"]["type"])
        self.assertEqual(
            "https://example.local:8080",
            auth_providers["ubuntu"]["saml_config"]["sp"]["entityId"],
        )
        auth_providers = literal_eval(updated_plan_env["INDICO_AUTH_PROVIDERS"])
        self.assertEqual("saml", auth_providers["ubuntu"]["type"])
        applied_saml_config = auth_providers["ubuntu"]["saml_config"]
        self.assertEqual("https://example.local:8080", applied_saml_config["sp"]["entityId"])
        self.assertEqual(saml_config.entity_id, applied_saml_config["idp"]["entityId"])
        self.assertEqual(saml_config.certificates[0], applied_saml_config["idp"]["x509cert"])
        self.assertEqual(
            str(saml_config.endpoints[0].url),
            applied_saml_config["idp"]["singleSignOnService"]["url"],
        )
        self.assertEqual(
            saml_config.endpoints[0].binding,
            applied_saml_config["idp"]["singleSignOnService"]["binding"],
        )
        self.assertNotIn("response_url", applied_saml_config["idp"]["singleSignOnService"])
        self.assertEqual(
            str(saml_config.endpoints[1].url),
            applied_saml_config["idp"]["singleLogoutService"]["url"],
        )
        self.assertEqual(
            saml_config.endpoints[1].binding,
            applied_saml_config["idp"]["singleLogoutService"]["binding"],
        )
        self.assertEqual(
            str(saml_config.endpoints[1].response_url),
            applied_saml_config["idp"]["singleLogoutService"]["response_url"],
        )

        identity_providers = literal_eval(updated_plan_env["INDICO_IDENTITY_PROVIDERS"])
        self.assertEqual("saml", identity_providers["ubuntu"]["type"])
        mock_exec.assert_any_call(
            ["git", "clone", "https://example.com/custom", "."],
            working_dir="/srv/indico/custom",
            user="indico",
            environment={},
        )
        mock_exec.assert_any_call(
            [
                "pip",
                "install",
                "--upgrade",
                "-c",
                "/tmp/constraints-123456.txt",  # nosec B108
                "git+https://example.git/#subdirectory=themes_cern",
            ],
            environment={},
        )

        self.harness.update_config({"site_url": "https://example.local"})
        # ops testing harness doesn't rerun the charm's __init__
        # manually rerun the _require_nginx_route function
        self.harness.charm._require_nginx_route()
        nginx_route_relation_data = self.harness.get_relation_data(
            self.nginx_route_relation_id, self.harness.charm.app
        )
        self.assertEqual("example.local", nginx_route_relation_data["service-hostname"])

    @patch.object(ops.Container, "exec")
    def test_config_changed_when_config_invalid(self, mock_exec):
        """
        arrange: charm created and relations established
        act: trigger an invalid site URL configuration change for the charm
        assert: the unit reaches blocked status
        """
        mock_exec.return_value = MagicMock(wait_output=MagicMock(return_value=("", None)))

        self.set_relations_and_leader()
        self.harness.update_config({"site_url": "example.local"})
        self.assertEqual(
            self.harness.model.unit.status,
            ops.BlockedStatus("Configuration option site_url is not valid"),
        )

    @patch.object(ops.Container, "exec")
    @patch("charm.secrets")
    def test_config_changed_with_external_resources(self, mock_secrets, mock_exec):
        """
        arrange: charm created and relations established
        act: configure the customization resources and external plugins
        assert: the sources are downloaded and the plugins installed
        """
        mock_exec.return_value = MagicMock(wait_output=MagicMock(return_value=("", None)))
        mock_secrets.token_hex.return_value = "123456"

        self.set_relations_and_leader()
        self.harness.update_config(
            {
                "customization_sources_url": "https://example.com/custom",
                "external_plugins": "git+https://example.git/#subdirectory=themes_cern",
            }
        )
        mock_exec.assert_any_call(
            ["git", "clone", "https://example.com/custom", "."],
            working_dir="/srv/indico/custom",
            user="indico",
            environment={},
        )
        mock_exec.assert_any_call(
            [
                "pip",
                "install",
                "--upgrade",
                "-c",
                "/tmp/constraints-123456.txt",  # nosec B108
                "git+https://example.git/#subdirectory=themes_cern",
            ],
            environment={},
        )

    def test_config_changed_when_pebble_not_ready(self):
        """
        arrange: charm created and relations established but pebble is not ready yet
        act: trigger a configuration change for the charm
        assert: the charm is still in waiting status
        """
        self.set_up_all_relations()
        self.harness.update_config({"indico_support_email": "example@email.local"})
        self.assertEqual(self.harness.model.unit.status, ops.WaitingStatus("Waiting for pebble"))

    @patch.object(ops.Container, "exec")
    def test_config_changed_when_saml_groups_plugin_installed(self, mock_exec):
        """
        arrange: charm created and relations established and saml_groups plugin installed
        act: trigger a configuration change with external_plugins for the charm
        assert: the indico identity provider is set to saml_groups
        """
        plugins_table = """
        +-----------------------+
        | Name        | Title   |
        +-------------+---------+
        | anonymize   | Anonymize.  |
        | autocreate  | Autocreate. |
        | piwik       | Piwik statistics |
        | saml_groups | SAML Groups Plugin. |
        | storage_s3  | S3 Storage |
        +-------------+---------+
        """.lstrip(
            "\n"
        )
        mock_exec.return_value = MagicMock(
            wait_output=MagicMock(return_value=(plugins_table, None))
        )

        self.set_relations_and_leader()

        saml_endpoints = (
            SamlEndpoint(
                name="SingleSignOnService",
                url="https://example.com/login",
                binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            ),
            SamlEndpoint(
                name="SingleLogoutService",
                url="https://example.com/logout",
                binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                response_url="https://example.com/response",
            ),
        )
        saml_config = SamlConfig(
            entity_id="entity",
            metadata_url="https://example.com/metadata",
            certificates=("cert1,", "cert2"),
            endpoints=saml_endpoints,
        )
        self.harness.charm.state.saml_config = saml_config
        self.harness.update_config(
            {
                "external_plugins": "git+https://example.git",
            }
        )

        updated_plan = self.harness.get_container_pebble_plan("indico").to_dict()
        updated_plan_env = updated_plan["services"]["indico"]["environment"]

        identity_providers = literal_eval(updated_plan_env["INDICO_IDENTITY_PROVIDERS"])
        self.assertEqual("saml_groups", identity_providers["ubuntu"]["type"])

    @patch.object(ops.JujuVersion, "from_environ")
    def test_on_leader_elected_when_secrets_not_supported(self, mock_juju_env):
        """
        arrange: charm created and secrets not supported
        act: trigger the leader elected event
        assert: the peer relation containers the secret-key
        """
        mock_juju_env.return_value = MagicMock(has_secrets=False)
        rel_id = self.harness.add_relation("indico-peers", self.harness.charm.app.name)
        self.harness.set_leader(True)
        secret_key = self.harness.get_relation_data(rel_id, self.harness.charm.app.name).get(
            "secret-key"
        )
        self.assertIsNotNone(secret_key)
        self.harness.set_leader(False)
        self.harness.set_leader(True)
        self.assertEqual(
            secret_key,
            self.harness.get_relation_data(rel_id, self.harness.charm.app.name).get("secret-key"),
        )

    @patch.object(ops.JujuVersion, "from_environ")
    def test_on_leader_elected_when_secrets_supported(self, mock_juju_env):
        """
        arrange: charm created and secrets supported
        act: trigger the leader elected event
        assert: the peer relation containers the secret-key
        """
        mock_juju_env.return_value = MagicMock(has_secrets=True)
        rel_id = self.harness.add_relation("indico-peers", self.harness.charm.app.name)
        self.harness.set_leader(True)
        secret_id = self.harness.get_relation_data(rel_id, self.harness.charm.app.name).get(
            "secret-id"
        )
        self.harness.set_leader(False)
        self.harness.set_leader(True)
        self.assertEqual(
            secret_id,
            self.harness.get_relation_data(rel_id, self.harness.charm.app.name).get("secret-id"),
        )

    @patch.object(ops.JujuVersion, "from_environ")
    def test_on_leader_elected_sets_celery_unit(self, mock_juju_env):
        """
        arrange: given a charm with an empty peer relation
        act: trigger the leader elected event
        assert: the peer relation containers the celery-unit
        """
        mock_juju_env.return_value = MagicMock(has_secrets=True)
        rel_id = self.harness.add_relation("indico-peers", self.harness.charm.app.name)
        self.harness.set_leader(True)
        celery_unit = self.harness.get_relation_data(rel_id, self.harness.charm.app.name).get(
            "celery-unit"
        )
        self.assertEqual(celery_unit, self.harness.charm.unit.name)

    @patch.object(ops.JujuVersion, "from_environ")
    def test_on_leader_elected_not_sets_celery_unit_when_existing(self, mock_juju_env):
        """
        arrange: given a charm with a peer relation with celery-unit in the databag
        act: trigger the leader elected
        assert: the stored celery-unit is not updated
        """
        mock_juju_env.return_value = MagicMock(has_secrets=True)
        rel_id = self.harness.add_relation(
            "indico-peers", self.harness.charm.app.name, app_data={"celery-unit": "example"}
        )
        self.harness.set_leader(True)
        celery_unit = self.harness.get_relation_data(rel_id, self.harness.charm.app.name).get(
            "celery-unit"
        )
        self.assertEqual(celery_unit, "example")

    @patch.object(ops.JujuVersion, "from_environ")
    def test_on_peer_relation_departed_no_celery_unit_relation_data_unchanged(self, mock_juju_env):
        """
        arrange: given a charm with two units and a peer relation with celery-unit in the databag
        act: remove a unit not matching the celery-unit
        assert: the stored celery-unit is not updated
        """
        mock_juju_env.return_value = MagicMock(has_secrets=True)
        rel_id = self.harness.add_relation(
            "indico-peers", self.harness.charm.app.name, app_data={"celery-unit": "example"}
        )
        self.harness.add_relation_unit(rel_id, "indico/0")
        self.harness.add_relation_unit(rel_id, "indico/1")
        self.harness.set_leader(True)
        celery_unit = self.harness.get_relation_data(rel_id, self.harness.charm.app.name).get(
            "celery-unit"
        )
        self.harness.remove_relation_unit(rel_id, "indico/1")
        self.assertEqual(celery_unit, "example")

    @patch.object(ops.JujuVersion, "from_environ")
    def test_on_peer_relation_departed_celery_unit_relation_data_changed(self, mock_juju_env):
        """
        arrange: given a charm with two units and a peer relation with celery-unit in the databag
        act: remove the unit matching the celery-unit
        assert: the stored celery-unit is updated
        """
        mock_juju_env.return_value = MagicMock(has_secrets=True)
        self.harness.set_can_connect(self.harness.model.unit.containers["indico"], True)
        rel_id = self.harness.add_relation(
            "indico-peers", self.harness.charm.app.name, app_data={"celery-unit": "indico/1"}
        )
        self.harness.add_relation_unit(rel_id, "indico/0")
        self.harness.add_relation_unit(rel_id, "indico/1")
        self.harness.set_leader(True)
        self.harness.remove_relation_unit(rel_id, "indico/1")
        celery_unit = self.harness.get_relation_data(rel_id, self.harness.charm.app.name).get(
            "celery-unit"
        )
        self.assertEqual(celery_unit, "indico/0")

    @patch.object(ops.JujuVersion, "from_environ")
    def test_on_peer_relation_departed_celery_leder_unit_relation_data_changed(
        self, mock_juju_env
    ):
        """
        arrange: given a charm with two units and a peer relation with celery-unit in the databag
        act: remove the leader unit matching the celery-unit
        assert: the stored celery-unit is removed
        """
        mock_juju_env.return_value = MagicMock(has_secrets=True)
        self.harness.set_can_connect(self.harness.model.unit.containers["indico"], True)
        rel_id = self.harness.add_relation(
            "indico-peers", self.harness.charm.app.name, app_data={"celery-unit": "indico/0"}
        )
        self.harness.add_relation_unit(rel_id, "indico/0")
        self.harness.add_relation_unit(rel_id, "indico/1")
        self.harness.set_leader(True)
        self.harness.remove_relation_unit(rel_id, "indico/0")
        celery_unit = self.harness.get_relation_data(rel_id, self.harness.charm.app.name).get(
            "celery-unit"
        )
        self.assertIsNone(celery_unit)

    @patch.object(ops.JujuVersion, "from_environ")
    @patch.object(ops.Container, "exec")
    def test_indico_pebble_ready_when_leader_includes_celery(self, mock_exec, mock_juju_env):
        """
        arrange: charm created, and relations established
        act: trigger container pebble ready event for the Indico container on a leader unit
        assert: the indico and celery services are running
        """
        mock_juju_env.return_value = MagicMock(has_secrets=False)
        mock_exec.return_value = MagicMock(wait_output=MagicMock(return_value=("", None)))
        self.set_up_all_relations()
        self.harness.set_leader(True)

        self.harness.container_pebble_ready("indico")

        updated_plan = self.harness.get_container_pebble_plan("indico").to_dict()
        assert "indico" in updated_plan["services"]
        assert "celery" in updated_plan["services"]

    @patch.object(ops.JujuVersion, "from_environ")
    @patch.object(ops.Container, "exec")
    def test_indico_pebble_ready_when_not_leader_doesnt_include_celery(
        self, mock_exec, mock_juju_env
    ):
        """
        arrange: charm created, and relations established
        act: trigger container pebble ready event for the Indico container on a non leader unit
        assert: the indico service is running and the celery service is not
        """
        mock_juju_env.return_value = MagicMock(has_secrets=False)
        mock_exec.return_value = MagicMock(wait_output=MagicMock(return_value=("", None)))
        self.set_up_all_relations()
        self.harness.set_leader(False)

        self.harness.container_pebble_ready("indico")

        updated_plan = self.harness.get_container_pebble_plan("indico").to_dict()
        assert "indico" in updated_plan["services"]
        assert "celery" not in updated_plan["services"]
