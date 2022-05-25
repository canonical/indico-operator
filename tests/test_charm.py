# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
import unittest

from charm import IndicoOperatorCharm
from ops.model import ActiveStatus, WaitingStatus
from ops.testing import Harness


class TestCharm(unittest.TestCase):
    def setUp(self):
        self.harness = Harness(IndicoOperatorCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def test_missing_relations(self):
        self.harness.update_config({"site_url": "foo"})
        self.assertEqual(self.harness.model.unit.status, WaitingStatus('Waiting for redis relation'))
        redis_relation_id = self.harness.add_relation('redis', self.harness.charm.app.name)
        self.harness.add_relation_unit(redis_relation_id, "redis/0")
        self.harness.update_relation_data(
            redis_relation_id, "redis/0", {"something": "just to trigger rel-changed event"}
        )
        self.assertEqual(self.harness.model.unit.status, WaitingStatus('Waiting for database relation'))
        # db_relation_id = self.harness.add_relation('db', 'postgresql')
        # self.harness.add_relation_unit(db_relation_id, "postgresql/0")
        # self.harness.update_relation_data(
        #     redis_relation_id, "postgresql/0", {"something": "just to trigger rel-changed event"}
        # )
        # self.assertEqual(self.harness.model.unit.status, WaitingStatus('Waiting for pebble'))

    def test_indico_nginx_pebble_ready(self):
        initial_plan = self.harness.get_container_pebble_plan("indico-nginx")
        self.assertEqual(initial_plan.to_yaml(), "{}\n")
        # Set relation data
        self.harness.charm._stored.db_uri = 'db-uri'
        self.harness.charm._stored.redis_relation = {1: {'hostname': 'redis-host', 'port': 1010}}

        expected_plan = {
            "services": {
                "indico-nginx": {
                    "override": "replace",
                    "summary": "Nginx service",
                    "command": "nginx",
                    "startup": "enabled",
                },
            },
        }

        container = self.harness.model.unit.get_container("indico-nginx")
        self.harness.charm.on.indico_nginx_pebble_ready.emit(container)
        updated_plan = self.harness.get_container_pebble_plan("indico-nginx").to_dict()
        self.assertEqual(expected_plan, updated_plan)
        service = self.harness.model.unit.get_container("indico-nginx").get_service("indico-nginx")
        self.assertTrue(service.is_running())
        self.assertEqual(self.harness.model.unit.status, WaitingStatus('Waiting for pebble'))

    def test_all_pebble_services_ready(self):
        # Set relation data
        self.harness.charm._stored.db_uri = 'db-uri'
        self.harness.charm._stored.redis_relation = {1: {'hostname': 'redis-host', 'port': 1010}}

        container = self.harness.model.unit.get_container("indico")
        self.harness.charm.on.indico_pebble_ready.emit(container)
        self.assertEqual(self.harness.model.unit.status, WaitingStatus('Waiting for pebble'))
        container = self.harness.model.unit.get_container("indico-celery")
        self.harness.charm.on.indico_celery_pebble_ready.emit(container)
        self.assertEqual(self.harness.model.unit.status, WaitingStatus('Waiting for pebble'))
        container = self.harness.model.unit.get_container("indico-nginx")
        self.harness.charm.on.indico_nginx_pebble_ready.emit(container)
        self.assertEqual(self.harness.model.unit.status, ActiveStatus())

    def test_indico_pebble_ready(self):
        initial_plan = self.harness.get_container_pebble_plan("indico")
        self.assertEqual(initial_plan.to_yaml(), "{}\n")
        # Set relation data
        self.harness.charm._stored.db_uri = 'db-uri'
        self.harness.charm._stored.redis_relation = {1: {'hostname': 'redis-host', 'port': 1010}}

        expected_plan = {
            "services": {
                "indico": {
                    "override": "replace",
                    "summary": "Indico service",
                    "command": "/srv/indico/.venv/bin/uwsgi --ini /etc/uwsgi.ini",
                    "startup": "enabled",
                    "environment": {
                        'INDICO_DB_URI': 'db-uri',
                        'CELERY_BROKER': 'redis://redis-host:1010',
                        'SECRET_KEY': self.harness.charm._stored.secret_key,
                        'SERVICE_HOSTNAME': "indico.local",
                        'SERVICE_PORT': 8081,
                        'REDIS_CACHE_URL': 'redis://redis-host:1010',
                        'SMTP_SERVER': '',
                        'SMTP_PORT': 25,
                        'SMTP_LOGIN': '',
                        'SMTP_PASSWORD': '',
                        'SMTP_USE_TLS': True,
                        'INDICO_SUPPORT_EMAIL': 'support-tech@mydomain.local',
                        'INDICO_PUBLIC_SUPPORT_EMAIL': 'support@mydomain.local',
                        'INDICO_NO_REPLY_EMAIL': 'noreply@mydomain.local',
                    },
                },
            },
        }

        container = self.harness.model.unit.get_container("indico")
        self.harness.charm.on.indico_pebble_ready.emit(container)
        updated_plan = self.harness.get_container_pebble_plan("indico").to_dict()
        self.assertEqual(expected_plan, updated_plan)
        service = self.harness.model.unit.get_container("indico").get_service("indico")
        self.assertTrue(service.is_running())
        self.assertEqual(self.harness.model.unit.status, WaitingStatus('Waiting for pebble'))

    def test_indico_celery_pebble_ready(self):
        initial_plan = self.harness.get_container_pebble_plan("indico-celery")
        self.assertEqual(initial_plan.to_yaml(), "{}\n")
        # Set relation data
        self.maxDiff = None
        self.harness.charm._stored.db_uri = 'db-uri'
        self.harness.charm._stored.redis_relation = {1: {'hostname': 'redis-host', 'port': 1010}}

        expected_plan = {
            "services": {
                "indico-celery": {
                    "override": "replace",
                    "summary": "Indico celery",
                    "command": "/srv/indico/.venv/bin/indico celery worker -B --uid 2000",
                    "startup": "enabled",
                    "environment": {
                        'INDICO_DB_URI': 'db-uri',
                        'CELERY_BROKER': 'redis://redis-host:1010',
                        'SECRET_KEY': self.harness.charm._stored.secret_key,
                        'SERVICE_HOSTNAME': "indico.local",
                        'SERVICE_PORT': 8081,
                        'REDIS_CACHE_URL': 'redis://redis-host:1010',
                        'SMTP_SERVER': '',
                        'SMTP_PORT': 25,
                        'SMTP_LOGIN': '',
                        'SMTP_PASSWORD': '',
                        'SMTP_USE_TLS': True,
                        'INDICO_SUPPORT_EMAIL': 'support-tech@mydomain.local',
                        'INDICO_PUBLIC_SUPPORT_EMAIL': 'support@mydomain.local',
                        'INDICO_NO_REPLY_EMAIL': 'noreply@mydomain.local',
                    },
                },
            },
        }

        container = self.harness.model.unit.get_container("indico-celery")
        self.harness.charm.on.indico_celery_pebble_ready.emit(container)
        updated_plan = self.harness.get_container_pebble_plan("indico-celery").to_dict()
        self.assertEqual(expected_plan, updated_plan)
        service = self.harness.model.unit.get_container("indico-celery").get_service("indico-celery")
        self.assertTrue(service.is_running())
        self.assertEqual(self.harness.model.unit.status, WaitingStatus('Waiting for pebble'))

    def test_config_changed(self):
        # Set relation data
        self.harness.charm._stored.db_uri = 'db-uri'
        self.harness.charm._stored.redis_relation = {1: {'hostname': 'redis-host', 'port': 1010}}
        self.harness.disable_hooks()
        self.harness.set_leader(True)
        self.harness.enable_hooks()

        container = self.harness.model.unit.get_container("indico")
        self.harness.charm.on.indico_pebble_ready.emit(container)
        container = self.harness.model.unit.get_container("indico-celery")
        self.harness.charm.on.indico_celery_pebble_ready.emit(container)
        container = self.harness.model.unit.get_container("indico-nginx")
        self.harness.charm.on.indico_nginx_pebble_ready.emit(container)
        self.harness.update_config(
            {
                "indico_support_email": "example@email.local",
                "indico_public_support_email": "public@email.local",
                "indico_no_reply_email": "noreply@email.local",
                "site_url": "http://example.local",
                "smtp_server": "localhost",
                "smtp_port": 8025,
                "smtp_login": "user",
                "smtp_password": "pass",
                "smtp_use_tls": False,
            }
        )

        expected_plan = {
            "services": {
                "indico": {
                    "override": "replace",
                    "summary": "Indico service",
                    "command": "/srv/indico/.venv/bin/uwsgi --ini /etc/uwsgi.ini",
                    "startup": "enabled",
                    "environment": {
                        'INDICO_DB_URI': 'db-uri',
                        'CELERY_BROKER': 'redis://redis-host:1010',
                        'SECRET_KEY': self.harness.charm._stored.secret_key,
                        'SERVICE_HOSTNAME': "example.local",
                        'SERVICE_PORT': 8081,
                        'REDIS_CACHE_URL': 'redis://redis-host:1010',
                        'SMTP_SERVER': 'localhost',
                        'SMTP_PORT': 8025,
                        'SMTP_LOGIN': 'user',
                        'SMTP_PASSWORD': 'pass',
                        'SMTP_USE_TLS': False,
                        'INDICO_SUPPORT_EMAIL': 'example@email.local',
                        'INDICO_PUBLIC_SUPPORT_EMAIL': 'public@email.local',
                        'INDICO_NO_REPLY_EMAIL': 'noreply@email.local',
                    },
                },
            },
        }
        updated_plan = self.harness.get_container_pebble_plan("indico").to_dict()
        self.assertEqual(expected_plan, updated_plan)

        expected_plan = {
            "services": {
                "indico-celery": {
                    "override": "replace",
                    "summary": "Indico celery",
                    "command": "/srv/indico/.venv/bin/indico celery worker -B --uid 2000",
                    "startup": "enabled",
                    "environment": {
                        'INDICO_DB_URI': 'db-uri',
                        'CELERY_BROKER': 'redis://redis-host:1010',
                        'SECRET_KEY': self.harness.charm._stored.secret_key,
                        'SERVICE_HOSTNAME': "example.local",
                        'SERVICE_PORT': 8081,
                        'REDIS_CACHE_URL': 'redis://redis-host:1010',
                        'SMTP_SERVER': 'localhost',
                        'SMTP_PORT': 8025,
                        'SMTP_LOGIN': 'user',
                        'SMTP_PASSWORD': 'pass',
                        'SMTP_USE_TLS': False,
                        'INDICO_SUPPORT_EMAIL': 'example@email.local',
                        'INDICO_PUBLIC_SUPPORT_EMAIL': 'public@email.local',
                        'INDICO_NO_REPLY_EMAIL': 'noreply@email.local',
                    },
                },
            },
        }

        updated_plan = self.harness.get_container_pebble_plan("indico-celery").to_dict()
        self.assertEqual(expected_plan, updated_plan)

        self.assertEqual('example.local', self.harness.charm.ingress.config_dict['service-hostname'])

    def test_config_changed_when_pebble_not_ready(self):
        # Set relation data
        self.harness.charm._stored.db_uri = 'db-uri'
        self.harness.charm._stored.redis_relation = {1: {'hostname': 'redis-host', 'port': 1010}}

        self.harness.update_config({"indico_support_email": "example@email.local"})
        self.assertEqual(self.harness.model.unit.status, WaitingStatus('Waiting for pebble'))
