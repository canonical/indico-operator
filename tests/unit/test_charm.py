# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import unittest
from unittest.mock import MagicMock, patch

from ops.model import ActiveStatus, Container, WaitingStatus
from ops.testing import Harness

from charm import IndicoOperatorCharm


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(IndicoOperatorCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_missing_relations(self):
        self.harness.update_config({"site_url": "foo"})
        self.assertEqual(
            self.harness.model.unit.status, WaitingStatus("Waiting for redis relation")
        )
        redis_relation_id = self.harness.add_relation("redis", self.harness.charm.app.name)
        self.harness.add_relation_unit(redis_relation_id, "redis/0")
        self.harness.update_relation_data(
            redis_relation_id, "redis/0", {"something": "just to trigger rel-changed event"}
        )
        self.assertEqual(
            self.harness.model.unit.status, WaitingStatus("Waiting for database relation")
        )

    def test_indico_nginx_pebble_ready(self):
        initial_plan = self.harness.get_container_pebble_plan("indico-nginx")
        self.assertEqual(initial_plan.to_yaml(), "{}\n")
        # Set relation data
        self.harness.charm._stored.db_uri = "db-uri"
        self.harness.charm._stored.redis_relation = {1: {"hostname": "redis-host", "port": 1010}}

        container = self.harness.model.unit.get_container("indico-nginx")
        self.harness.charm.on.indico_nginx_pebble_ready.emit(container)

        service = self.harness.model.unit.get_container("indico-nginx").get_service("indico-nginx")
        self.assertTrue(service.is_running())
        self.assertEqual(self.harness.model.unit.status, WaitingStatus("Waiting for pebble"))

    def test_all_pebble_services_ready(self):
        # Set relation data
        self.harness.charm._stored.db_uri = "db-uri"
        self.harness.charm._stored.redis_relation = {1: {"hostname": "redis-host", "port": 1010}}

        container = self.harness.model.unit.get_container("indico")
        self.harness.charm.on.indico_pebble_ready.emit(container)
        self.assertEqual(self.harness.model.unit.status, WaitingStatus("Waiting for pebble"))
        container = self.harness.model.unit.get_container("indico-celery")
        self.harness.charm.on.indico_celery_pebble_ready.emit(container)
        self.assertEqual(self.harness.model.unit.status, WaitingStatus("Waiting for pebble"))
        container = self.harness.model.unit.get_container("indico-nginx")
        self.harness.charm.on.indico_nginx_pebble_ready.emit(container)
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())

    def test_indico_pebble_ready(self):
        initial_plan = self.harness.get_container_pebble_plan("indico")
        self.assertEqual(initial_plan.to_yaml(), "{}\n")
        # Set relation data
        self.harness.charm._stored.db_uri = "db-uri"
        self.harness.charm._stored.redis_relation = {1: {"hostname": "redis-host", "port": 1010}}

        container = self.harness.model.unit.get_container("indico")
        self.harness.charm.on.indico_pebble_ready.emit(container)
        updated_plan = self.harness.get_container_pebble_plan("indico").to_dict()
        updated_plan_env = updated_plan["services"]["indico"]["environment"]

        self.assertEqual("db-uri", updated_plan_env["INDICO_DB_URI"])
        self.assertEqual("redis://redis-host:1010", updated_plan_env["CELERY_BROKER"])
        self.assertEqual(self.harness.charm._stored.secret_key, updated_plan_env["SECRET_KEY"])
        self.assertEqual("indico", updated_plan_env["SERVICE_HOSTNAME"])
        self.assertIsNone(updated_plan_env["SERVICE_PORT"])
        self.assertEqual("redis://redis-host:1010", updated_plan_env["REDIS_CACHE_URL"])
        self.assertEqual("support-tech@mydomain.local", updated_plan_env["INDICO_SUPPORT_EMAIL"])
        self.assertEqual("support@mydomain.local", updated_plan_env["INDICO_PUBLIC_SUPPORT_EMAIL"])
        self.assertEqual("noreply@mydomain.local", updated_plan_env["INDICO_NO_REPLY_EMAIL"])
        self.assertEqual("", updated_plan_env["SMTP_SERVER"])
        self.assertEqual(25, updated_plan_env["SMTP_PORT"])
        self.assertEqual("", updated_plan_env["SMTP_LOGIN"])
        self.assertEqual("", updated_plan_env["SMTP_PASSWORD"])
        self.assertTrue(updated_plan_env["SMTP_USE_TLS"])
        self.assertFalse(updated_plan_env["CUSTOMIZATION_DEBUG"])
        self.assertEqual("", updated_plan_env["INDICO_EXTRA_PLUGINS"])

        service = self.harness.model.unit.get_container("indico").get_service("indico")
        self.assertTrue(service.is_running())
        self.assertEqual(self.harness.model.unit.status, WaitingStatus("Waiting for pebble"))

    def test_indico_celery_pebble_ready(self):
        initial_plan = self.harness.get_container_pebble_plan("indico-celery")
        self.assertEqual(initial_plan.to_yaml(), "{}\n")
        # Set relation data
        self.maxDiff = None
        self.harness.charm._stored.db_uri = "db-uri"
        self.harness.charm._stored.redis_relation = {1: {"hostname": "redis-host", "port": 1010}}

        container = self.harness.model.unit.get_container("indico-celery")
        self.harness.charm.on.indico_celery_pebble_ready.emit(container)
        updated_plan = self.harness.get_container_pebble_plan("indico-celery").to_dict()
        updated_plan_env = updated_plan["services"]["indico-celery"]["environment"]

        self.assertEqual("db-uri", updated_plan_env["INDICO_DB_URI"])
        self.assertEqual("redis://redis-host:1010", updated_plan_env["CELERY_BROKER"])
        self.assertEqual(self.harness.charm._stored.secret_key, updated_plan_env["SECRET_KEY"])
        self.assertEqual("indico", updated_plan_env["SERVICE_HOSTNAME"])
        self.assertEqual("http", updated_plan_env["SERVICE_SCHEME"])
        self.assertIsNone(updated_plan_env["SERVICE_PORT"])
        self.assertEqual("redis://redis-host:1010", updated_plan_env["REDIS_CACHE_URL"])
        self.assertEqual("support-tech@mydomain.local", updated_plan_env["INDICO_SUPPORT_EMAIL"])
        self.assertEqual("support@mydomain.local", updated_plan_env["INDICO_PUBLIC_SUPPORT_EMAIL"])
        self.assertEqual("noreply@mydomain.local", updated_plan_env["INDICO_NO_REPLY_EMAIL"])
        self.assertEqual("", updated_plan_env["SMTP_SERVER"])
        self.assertEqual(25, updated_plan_env["SMTP_PORT"])
        self.assertEqual("", updated_plan_env["SMTP_LOGIN"])
        self.assertEqual("", updated_plan_env["SMTP_PASSWORD"])
        self.assertTrue(updated_plan_env["SMTP_USE_TLS"])
        self.assertFalse(updated_plan_env["CUSTOMIZATION_DEBUG"])
        self.assertEqual("", updated_plan_env["INDICO_EXTRA_PLUGINS"])

        service = self.harness.model.unit.get_container("indico-celery").get_service(
            "indico-celery"
        )
        self.assertTrue(service.is_running())
        self.assertEqual(self.harness.model.unit.status, WaitingStatus("Waiting for pebble"))

    def test_config_changed(self):
        # Set relation data
        self.harness.charm._stored.db_uri = "db-uri"
        self.harness.charm._stored.redis_relation = {1: {"hostname": "redis-host", "port": 1010}}
        self.harness.disable_hooks()
        self.harness.set_leader(True)
        self.harness.enable_hooks()

        container = self.harness.model.unit.get_container("indico")
        self.harness.charm.on.indico_pebble_ready.emit(container)
        container = self.harness.model.unit.get_container("indico-celery")
        self.harness.charm.on.indico_celery_pebble_ready.emit(container)
        container = self.harness.model.unit.get_container("indico-nginx")
        self.harness.charm.on.indico_nginx_pebble_ready.emit(container)

        class MockExecProcess(object):
            wait_output = MagicMock(return_value=("", None))

        with patch.object(Container, "exec", return_value=MockExecProcess()):
            self.harness.update_config(
                {
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
                    "indico_extra_plugins": "storage_s3",
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
        self.assertEqual("storage_s3", updated_plan_env["INDICO_EXTRA_PLUGINS"])

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
        self.assertEqual("storage_s3", updated_plan_env["INDICO_EXTRA_PLUGINS"])

        self.harness.disable_hooks()
        self.harness.set_leader(True)
        self.harness.enable_hooks()

        with patch.object(Container, "exec", return_value=MockExecProcess()):
            self.harness.update_config({"site_url": "https://example.local"})
        self.assertEqual(
            "example.local", self.harness.charm.ingress.config_dict["service-hostname"]
        )

    def test_config_changed_when_pebble_not_ready(self):
        # Set relation data
        self.harness.charm._stored.db_uri = "db-uri"
        self.harness.charm._stored.redis_relation = {1: {"hostname": "redis-host", "port": 1010}}

        self.harness.update_config({"indico_support_email": "example@email.local"})
        self.assertEqual(self.harness.model.unit.status, WaitingStatus("Waiting for pebble"))
