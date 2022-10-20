# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import unittest
from ast import literal_eval
from unittest.mock import MagicMock, patch

from ops.model import ActiveStatus, BlockedStatus, Container, WaitingStatus
from ops.testing import Harness

from tests.unit._patched_charm import IndicoOperatorCharm, pgsql_patch


class MockExecProcess(object):
    wait_output = MagicMock(return_value=("", None))


class TestCharm(unittest.TestCase):
    def setUp(self):
        pgsql_patch.start()
        self.harness = Harness(IndicoOperatorCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def tearDown(self):
        pgsql_patch.stop()

    def test_missing_relations(self):
        self.harness.update_config({"site_url": "foo"})
        self.assertEqual(
            self.harness.model.unit.status, WaitingStatus("Waiting for redis-broker relation")
        )
        redis_relation_id = self.harness.add_relation("redis", "redis-broker")
        self.harness.add_relation_unit(redis_relation_id, "redis-broker/0")
        self.harness.update_relation_data(
            redis_relation_id, "redis-broker/0", {"something": "just to trigger rel-changed event"}
        )
        self.assertEqual(
            self.harness.model.unit.status, WaitingStatus("Waiting for redis-cache relation")
        )
        redis_relation_id = self.harness.add_relation("redis", "redis-cache")
        self.harness.add_relation_unit(redis_relation_id, "redis-cache/0")
        self.harness.update_relation_data(
            redis_relation_id, "redis-cache/0", {"something": "just to trigger rel-changed event"}
        )
        self.assertEqual(
            self.harness.model.unit.status, WaitingStatus("Waiting for database relation")
        )

    def test_indico_nginx_pebble_ready(self):
        self.set_up_all_relations()
        self.harness.set_leader(True)

        with patch.object(Container, "exec", return_value=MockExecProcess()):
            self.harness.container_pebble_ready("indico-nginx")

        service = self.harness.model.unit.get_container("indico-nginx").get_service("indico-nginx")
        self.assertTrue(service.is_running())
        self.assertEqual(self.harness.model.unit.status, WaitingStatus("Waiting for pebble"))

    def test_all_pebble_services_ready(self):
        self.set_up_all_relations()
        self.harness.set_leader(True)

        with patch.object(Container, "exec", return_value=MockExecProcess()):
            self.harness.container_pebble_ready("nginx-prometheus-exporter")
            self.assertEqual(self.harness.model.unit.status, WaitingStatus("Waiting for pebble"))
            self.harness.container_pebble_ready("indico")
            self.assertEqual(self.harness.model.unit.status, WaitingStatus("Waiting for pebble"))
            self.harness.container_pebble_ready("indico-celery")
            self.assertEqual(self.harness.model.unit.status, WaitingStatus("Waiting for pebble"))
            self.harness.container_pebble_ready("indico-nginx")
            self.assertEqual(self.harness.model.unit.status, ActiveStatus())

    def test_indico_pebble_ready(self):
        self.set_up_all_relations()
        self.harness.set_leader(True)

        with patch.object(Container, "exec", return_value=MockExecProcess()):
            self.harness.container_pebble_ready("indico")

        updated_plan = self.harness.get_container_pebble_plan("indico").to_dict()
        updated_plan_env = updated_plan["services"]["indico"]["environment"]
        self.assertEqual("db-uri", updated_plan_env["INDICO_DB_URI"])
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
        self.assertEqual("", updated_plan_env["SMTP_SERVER"])
        self.assertEqual(25, updated_plan_env["SMTP_PORT"])
        self.assertEqual("", updated_plan_env["SMTP_LOGIN"])
        self.assertEqual("", updated_plan_env["SMTP_PASSWORD"])
        self.assertTrue(updated_plan_env["SMTP_USE_TLS"])
        self.assertFalse(updated_plan_env["CUSTOMIZATION_DEBUG"])
        self.assertEqual("default", updated_plan_env["ATTACHMENT_STORAGE"])
        storage_dict = literal_eval(updated_plan_env["STORAGE_DICT"])
        self.assertEqual("fs:/srv/indico/archive", storage_dict["default"])

        service = self.harness.model.unit.get_container("indico").get_service("indico")
        self.assertTrue(service.is_running())
        self.assertEqual(self.harness.model.unit.status, WaitingStatus("Waiting for pebble"))

    def test_indico_celery_pebble_ready(self):
        self.set_up_all_relations()
        self.harness.set_leader(True)

        with patch.object(Container, "exec", return_value=MockExecProcess()):
            self.harness.container_pebble_ready("indico-celery")

        updated_plan = self.harness.get_container_pebble_plan("indico-celery").to_dict()
        updated_plan_env = updated_plan["services"]["indico-celery"]["environment"]
        self.assertEqual("db-uri", updated_plan_env["INDICO_DB_URI"])
        self.assertEqual("redis://broker-host:1010", updated_plan_env["CELERY_BROKER"])
        peer_relation = self.harness.model.get_relation("indico-peers")
        self.assertEqual(
            self.harness.get_relation_data(peer_relation.id, self.harness.charm.app.name).get(
                "secret-key"
            ),
            updated_plan_env["SECRET_KEY"],
        )
        self.assertEqual("indico.local", updated_plan_env["SERVICE_HOSTNAME"])
        self.assertEqual("http", updated_plan_env["SERVICE_SCHEME"])
        self.assertIsNone(updated_plan_env["SERVICE_PORT"])
        self.assertEqual("redis://cache-host:1011", updated_plan_env["REDIS_CACHE_URL"])
        self.assertFalse(updated_plan_env["ENABLE_ROOMBOOKING"])
        self.assertEqual("support-tech@mydomain.local", updated_plan_env["INDICO_SUPPORT_EMAIL"])
        self.assertEqual("support@mydomain.local", updated_plan_env["INDICO_PUBLIC_SUPPORT_EMAIL"])
        self.assertEqual("noreply@mydomain.local", updated_plan_env["INDICO_NO_REPLY_EMAIL"])
        self.assertEqual("", updated_plan_env["SMTP_SERVER"])
        self.assertEqual(25, updated_plan_env["SMTP_PORT"])
        self.assertEqual("", updated_plan_env["SMTP_LOGIN"])
        self.assertEqual("", updated_plan_env["SMTP_PASSWORD"])
        self.assertTrue(updated_plan_env["SMTP_USE_TLS"])
        self.assertFalse(updated_plan_env["CUSTOMIZATION_DEBUG"])
        self.assertEqual("default", updated_plan_env["ATTACHMENT_STORAGE"])
        storage_dict = literal_eval(updated_plan_env["STORAGE_DICT"])
        self.assertEqual("fs:/srv/indico/archive", storage_dict["default"])
        self.assertFalse(literal_eval(updated_plan_env["INDICO_AUTH_PROVIDERS"]))
        self.assertFalse(literal_eval(updated_plan_env["INDICO_IDENTITY_PROVIDERS"]))

        service = self.harness.model.unit.get_container("indico-celery").get_service(
            "indico-celery"
        )
        self.assertTrue(service.is_running())
        self.assertEqual(self.harness.model.unit.status, WaitingStatus("Waiting for pebble"))

    def test_config_changed(self):
        self.set_up_all_relations()
        self.harness.set_leader(True)

        with patch.object(Container, "exec", return_value=MockExecProcess()) as exec_mock:
            self.harness.container_pebble_ready("nginx-prometheus-exporter")
            self.harness.container_pebble_ready("indico")
            self.harness.container_pebble_ready("indico-celery")
            self.harness.container_pebble_ready("indico-nginx")
            self.harness.update_config(
                {
                    "customization_debug": True,
                    "customization_sources_url": "https://example.com/custom",
                    "enable_roombooking": True,
                    "external_plugins": "git+https://example.git/#subdirectory=themes_cern",
                    "http_proxy": "http://squid.internal:3128",
                    "https_proxy": "https://squid.internal:3128",
                    "indico_support_email": "example@email.local",
                    "indico_public_support_email": "public@email.local",
                    "indico_no_reply_email": "noreply@email.local",
                    "saml_target_url": "https://login.ubuntu.com/saml/",
                    "site_url": "https://example.local:8080",
                    "smtp_server": "localhost",
                    "smtp_port": 8025,
                    "smtp_login": "user",
                    "smtp_password": "pass",
                    "smtp_use_tls": False,
                    "s3_storage": "s3:bucket=test-bucket,access_key=12345,secret_key=topsecret",
                }
            )

        updated_plan = self.harness.get_container_pebble_plan("indico").to_dict()
        updated_plan_env = updated_plan["services"]["indico"]["environment"]

        self.assertEqual("example.local", updated_plan_env["SERVICE_HOSTNAME"])
        self.assertEqual("http://squid.internal:3128", updated_plan_env["HTTP_PROXY"])
        self.assertEqual("https://squid.internal:3128", updated_plan_env["HTTPS_PROXY"])
        self.assertTrue(updated_plan_env["ENABLE_ROOMBOOKING"])
        self.assertEqual("example@email.local", updated_plan_env["INDICO_SUPPORT_EMAIL"])
        self.assertEqual("public@email.local", updated_plan_env["INDICO_PUBLIC_SUPPORT_EMAIL"])
        self.assertEqual("noreply@email.local", updated_plan_env["INDICO_NO_REPLY_EMAIL"])
        self.assertEqual("https", updated_plan_env["SERVICE_SCHEME"])
        self.assertEqual(8080, updated_plan_env["SERVICE_PORT"])
        self.assertEqual("localhost", updated_plan_env["SMTP_SERVER"])
        self.assertEqual(8025, updated_plan_env["SMTP_PORT"])
        self.assertEqual("user", updated_plan_env["SMTP_LOGIN"])
        self.assertEqual("pass", updated_plan_env["SMTP_PASSWORD"])
        self.assertFalse(updated_plan_env["SMTP_USE_TLS"])
        self.assertTrue(updated_plan_env["CUSTOMIZATION_DEBUG"])
        storage_dict = literal_eval(updated_plan_env["STORAGE_DICT"])
        self.assertEqual("s3", updated_plan_env["ATTACHMENT_STORAGE"])
        self.assertEqual("fs:/srv/indico/archive", storage_dict["default"])
        self.assertEqual(
            "s3:bucket=test-bucket,access_key=12345,secret_key=topsecret",
            storage_dict["s3"],
        )
        exec_mock.assert_any_call(
            ["git", "clone", "https://example.com/custom", "."],
            working_dir="/srv/indico/custom",
            user="indico",
            environment={
                "HTTP_PROXY": "http://squid.internal:3128",
                "HTTPS_PROXY": "https://squid.internal:3128",
            },
        )
        exec_mock.assert_any_call(
            ["pip", "install", "--upgrade", "git+https://example.git/#subdirectory=themes_cern"],
            environment={
                "HTTP_PROXY": "http://squid.internal:3128",
                "HTTPS_PROXY": "https://squid.internal:3128",
            },
        )

        updated_plan = self.harness.get_container_pebble_plan("indico-celery").to_dict()
        updated_plan_env = updated_plan["services"]["indico-celery"]["environment"]

        self.assertEqual("example.local", updated_plan_env["SERVICE_HOSTNAME"])
        self.assertEqual("http://squid.internal:3128", updated_plan_env["HTTP_PROXY"])
        self.assertEqual("https://squid.internal:3128", updated_plan_env["HTTPS_PROXY"])
        self.assertTrue(updated_plan_env["ENABLE_ROOMBOOKING"])
        self.assertEqual("example@email.local", updated_plan_env["INDICO_SUPPORT_EMAIL"])
        self.assertEqual("public@email.local", updated_plan_env["INDICO_PUBLIC_SUPPORT_EMAIL"])
        self.assertEqual("noreply@email.local", updated_plan_env["INDICO_NO_REPLY_EMAIL"])
        self.assertEqual("example.local", updated_plan_env["SERVICE_HOSTNAME"])
        self.assertEqual("https", updated_plan_env["SERVICE_SCHEME"])
        self.assertEqual(8080, updated_plan_env["SERVICE_PORT"])
        self.assertEqual("localhost", updated_plan_env["SMTP_SERVER"])
        self.assertEqual(8025, updated_plan_env["SMTP_PORT"])
        self.assertEqual("user", updated_plan_env["SMTP_LOGIN"])
        self.assertEqual("pass", updated_plan_env["SMTP_PASSWORD"])
        self.assertFalse(updated_plan_env["SMTP_USE_TLS"])
        self.assertTrue(updated_plan_env["CUSTOMIZATION_DEBUG"])
        self.assertEqual("s3", updated_plan_env["ATTACHMENT_STORAGE"])
        storage_dict = literal_eval(updated_plan_env["STORAGE_DICT"])
        self.assertEqual("fs:/srv/indico/archive", storage_dict["default"])
        self.assertEqual(
            "s3:bucket=test-bucket,access_key=12345,secret_key=topsecret",
            storage_dict["s3"],
        )
        auth_providers = literal_eval(updated_plan_env["INDICO_AUTH_PROVIDERS"])
        self.assertEqual("saml", auth_providers["ubuntu"]["type"])
        self.assertEqual(
            "https://example.local:8080",
            auth_providers["ubuntu"]["saml_config"]["sp"]["entityId"],
        )
        identity_providers = literal_eval(updated_plan_env["INDICO_IDENTITY_PROVIDERS"])
        self.assertEqual("saml", identity_providers["ubuntu"]["type"])

        with patch.object(Container, "exec", return_value=MockExecProcess()):
            self.harness.update_config({"site_url": "https://example.local"})
        self.assertEqual(
            "example.local", self.harness.charm.ingress.config_dict["service-hostname"]
        )

    def test_config_changed_when_config_invalid(self):
        self.set_up_all_relations()
        self.harness.set_leader(True)

        with patch.object(Container, "exec", return_value=MockExecProcess()):
            self.harness.container_pebble_ready("nginx-prometheus-exporter")
            self.harness.container_pebble_ready("indico")
            self.harness.container_pebble_ready("indico-celery")
            self.harness.container_pebble_ready("indico-nginx")
        self.harness.update_config({"site_url": "example.local"})
        self.assertEqual(
            self.harness.model.unit.status,
            BlockedStatus("Configuration option site_url is not valid"),
        )

    def test_config_changed_when_http_proxy_config_not_present(self):
        self.set_up_all_relations()
        self.harness.set_leader(True)

        with patch.object(Container, "exec", return_value=MockExecProcess()) as exec_mock:
            self.harness.container_pebble_ready("nginx-prometheus-exporter")
            self.harness.container_pebble_ready("indico")
            self.harness.container_pebble_ready("indico-celery")
            self.harness.container_pebble_ready("indico-nginx")
            self.harness.update_config(
                {
                    "customization_sources_url": "https://example.com/custom",
                    "external_plugins": "git+https://example.git/#subdirectory=themes_cern",
                }
            )

        exec_mock.assert_any_call(
            ["git", "clone", "https://example.com/custom", "."],
            working_dir="/srv/indico/custom",
            user="indico",
            environment=None,
        )
        exec_mock.assert_any_call(
            ["pip", "install", "--upgrade", "git+https://example.git/#subdirectory=themes_cern"],
            environment=None,
        )

    def test_config_changed_when_pebble_not_ready(self):
        self.set_up_all_relations()
        self.harness.update_config({"indico_support_email": "example@email.local"})
        self.assertEqual(self.harness.model.unit.status, WaitingStatus("Waiting for pebble"))

    def test_config_changed_when_saml_target_url_invalid(self):
        self.set_up_all_relations()
        self.harness.set_leader(True)

        with patch.object(Container, "exec", return_value=MockExecProcess()):
            self.harness.container_pebble_ready("indico")
            self.harness.container_pebble_ready("indico-celery")
            self.harness.container_pebble_ready("indico-nginx")

        self.harness.update_config({"saml_target_url": "sample.com/saml"})
        self.assertEqual(
            self.harness.model.unit.status.name,
            BlockedStatus.name,
        )
        self.assertTrue("Invalid saml_target_url option" in self.harness.model.unit.status.message)

    def test_pebble_ready_when_relations_not_ready(self):
        self.harness.container_pebble_ready("indico")
        self.harness.container_pebble_ready("indico-celery")
        self.harness.container_pebble_ready("indico-nginx")

        self.assertEqual(
            self.harness.model.unit.status, WaitingStatus("Waiting for redis-broker relation")
        )

    def test_on_leader_elected(self):
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

    def test_db_relations(self):
        self.set_up_all_relations()
        self.harness.set_leader(True)
        # testing harness not re-emits deferred events, manually trigger that
        self.harness.framework.reemit()
        db_relation_data = self.harness.get_relation_data(
            self.db_relation_id, self.harness.charm.app.name
        )
        self.assertEqual(
            db_relation_data.get("database"),
            "indico",
            "database name should be set after relation joined",
        )
        self.assertSetEqual(
            {"pg_trgm:public", "unaccent:public"},
            set(db_relation_data.get("extensions").split(",")),
            "database roles should be set after relation joined",
        )
        self.harness.update_relation_data(
            self.db_relation_id,
            "postgresql/0",
            {"master": "host=master"},
        )
        self.assertEqual(
            self.harness.charm._stored.db_uri,
            "postgresql://master",
            "database connection string should be set after database master ready",
        )
        self.harness.update_relation_data(
            self.db_relation_id,
            "postgresql/0",
            {"master": "host=new_master"},
        )
        self.assertEqual(
            self.harness.charm._stored.db_uri,
            "postgresql://new_master",
            "database connection string should change after database master changed",
        )

    @unittest.skip
    def test_refresh_external_resources_when_customization_and_plugins_set(self):
        self.harness.disable_hooks()
        self.set_up_all_relations()
        self.harness.set_leader(True)

        with patch.object(Container, "exec", return_value=MockExecProcess()) as exec_mock:
            self.harness.container_pebble_ready("nginx-prometheus-exporter")
            self.harness.container_pebble_ready("indico")
            self.harness.container_pebble_ready("indico-celery")
            self.harness.container_pebble_ready("indico-nginx")
            self.harness.update_config(
                {
                    "customization_sources_url": "https://example.com/custom",
                    "external_plugins": "git+https://example.git/#subdirectory=themes_cern",
                }
            )
            self.harness.charm.on.update_status.emit()

        exec_mock.assert_any_call(
            ["git", "pull"],
            working_dir="/srv/indico/custom",
            user="indico",
            environment=None,
        )
        exec_mock.assert_any_call(
            ["pip", "install", "--upgrade", "git+https://example.git/#subdirectory=themes_cern"],
            environment=None,
        )

    def set_up_all_relations(self):
        self.harness.charm._stored.db_uri = "db-uri"
        self.db_relation_id = self.harness.add_relation("db", "postgresql")
        self.harness.add_relation_unit(self.db_relation_id, "postgresql/0")

        self.harness.add_relation("indico-peers", self.harness.charm.app.name)

        broker_relation_id = self.harness.add_relation("redis", "redis-broker")
        self.harness.add_relation_unit(broker_relation_id, "redis-broker/0")

        cache_relation_id = self.harness.add_relation("redis", "redis-cache")
        self.harness.add_relation_unit(cache_relation_id, "redis-cache/0")

        cache_relation = self.harness.model.get_relation("redis", cache_relation_id)
        cache_unit = self.harness.model.get_unit("redis-cache/0")
        cache_relation.data = {cache_unit: {"hostname": "cache-host", "port": 1011}}

        broker_relation = self.harness.model.get_relation("redis", broker_relation_id)
        broker_unit = self.harness.model.get_unit("redis-broker/0")
        broker_relation.data = {broker_unit: {"hostname": "broker-host", "port": 1010}}
