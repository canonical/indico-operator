# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import unittest
from ast import literal_eval
from unittest.mock import MagicMock, patch

from ops.model import ActiveStatus, BlockedStatus, Container, WaitingStatus
from ops.testing import Harness

from charm import IndicoOperatorCharm


class MockExecProcess(object):
    wait_output = MagicMock(return_value=("", None))


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(IndicoOperatorCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()
        self.harness.charm.db = None

    def test_missing_relations(self):
        self.harness.update_config({"site_url": "foo"})
        self.assertEqual(
            self.harness.model.unit.status, WaitingStatus("Waiting for redis-broker relation")
        )
        redis_relation_id = self.harness.add_relation("redis", self.harness.charm.app.name)
        self.harness.add_relation_unit(redis_relation_id, "redis-broker/0")
        self.harness.update_relation_data(
            redis_relation_id, "redis-broker/0", {"something": "just to trigger rel-changed event"}
        )
        self.assertEqual(
            self.harness.model.unit.status, WaitingStatus("Waiting for redis-cache relation")
        )
        redis_relation_id = self.harness.add_relation("redis", self.harness.charm.app.name)
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
        self.assertEqual("indico", updated_plan_env["SERVICE_HOSTNAME"])
        self.assertIsNone(updated_plan_env["SERVICE_PORT"])
        self.assertEqual("redis://cache-host:1011", updated_plan_env["REDIS_CACHE_URL"])
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
        self.assertEqual("indico", updated_plan_env["SERVICE_HOSTNAME"])
        self.assertEqual("http", updated_plan_env["SERVICE_SCHEME"])
        self.assertIsNone(updated_plan_env["SERVICE_PORT"])
        self.assertEqual("redis://cache-host:1011", updated_plan_env["REDIS_CACHE_URL"])
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

        with patch.object(Container, "exec", return_value=MockExecProcess()):
            self.harness.container_pebble_ready("indico")
            self.harness.container_pebble_ready("indico-celery")
            self.harness.container_pebble_ready("indico-nginx")
            self.harness.update_config(
                {
                    "external_plugins": "git+https://example.git/#subdirectory=themes_cern",
                    "indico_support_email": "example@email.local",
                    "indico_public_support_email": "public@email.local",
                    "indico_no_reply_email": "noreply@email.local",
                    "site_url": "https://example.local:8080",
                    "smtp_server": "localhost",
                    "smtp_port": 8025,
                    "smtp_login": "user",
                    "smtp_password": "pass",
                    "smtp_use_tls": False,
                    "customization_debug": True,
                    "customization_sources_url": "https://example.com/custom",
                    "s3_storage": "s3:bucket=my-indico-test-bucket,access_key=12345,secret_key=topsecret",
                    "saml_target_url": "https://login.ubuntu.com/saml/",
                }
            )

        updated_plan = self.harness.get_container_pebble_plan("indico").to_dict()
        updated_plan_env = updated_plan["services"]["indico"]["environment"]

        self.assertEqual("example.local", updated_plan_env["SERVICE_HOSTNAME"])
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
        storage_dict = literal_eval(updated_plan_env["STORAGE_DICT"])
        self.assertEqual("s3", updated_plan_env["ATTACHMENT_STORAGE"])
        self.assertEqual("fs:/srv/indico/archive", storage_dict["default"])
        self.assertEqual(
            "s3:bucket=my-indico-test-bucket,access_key=12345,secret_key=topsecret",
            storage_dict["s3"],
        )

        updated_plan = self.harness.get_container_pebble_plan("indico-celery").to_dict()
        updated_plan_env = updated_plan["services"]["indico-celery"]["environment"]

        self.assertEqual("example.local", updated_plan_env["SERVICE_HOSTNAME"])
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
            "s3:bucket=my-indico-test-bucket,access_key=12345,secret_key=topsecret",
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
            "example.local", self.harness.charm._ingress.config_dict["service-hostname"]
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
            self.harness.model.unit.status,
            BlockedStatus(
                "Invalid saml_target_url option provided. Only https://login.ubuntu.com/saml/ is available."
            ),
        )

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
        self.assertIsNotNone(
            self.harness.get_relation_data(rel_id, self.harness.charm.app.name).get("secret-key")
        )

    def set_up_all_relations(self):
        self.harness.charm._stored.db_uri = "db-uri"
        self.harness.add_relation("indico-peers", self.harness.charm.app.name)
        broker_relation_id = self.harness.add_relation("redis", self.harness.charm.app.name)
        self.harness.add_relation_unit(broker_relation_id, "redis-broker/0")
        cache_relation_id = self.harness.add_relation("redis", self.harness.charm.app.name)
        self.harness.add_relation_unit(cache_relation_id, "redis-cache/0")
        self.harness.charm._stored.redis_relation = {
            broker_relation_id: {"hostname": "broker-host", "port": 1010},
            cache_relation_id: {"hostname": "cache-host", "port": 1011},
        }
