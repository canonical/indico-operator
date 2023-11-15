# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Indico charm unit tests."""

# pylint:disable=protected-access

import unittest
from typing import List

from ops.testing import Harness

from charm import IndicoOperatorCharm


class TestBase(unittest.TestCase):
    """Indico charm unit tests."""

    def setUp(self):
        """Set up test environment."""
        self.harness = Harness(IndicoOperatorCharm)
        self.addCleanup(self.harness.cleanup)
        self.harness.begin()

    def set_up_all_relations(self):
        """Set up all relations for the charm."""
        self.db_relation_id = self.harness.add_relation(  # pylint: disable=W0201
            "database", "postgresql"
        )
        self.harness.add_relation_unit(self.db_relation_id, "postgresql/0")
        self.harness.update_relation_data(
            self.db_relation_id,
            "postgresql",
            {
                "database": "indico",
                "endpoints": "postgresql-k8s-primary.local:5432",
                "password": "somepass",
                "username": "user1",
            },
        )

        self.harness.add_relation("indico-peers", self.harness.charm.app.name)

        broker_relation_id = self.harness.add_relation("redis-broker", "redis-broker")
        self.harness.add_relation_unit(broker_relation_id, "redis-broker/0")

        cache_relation_id = self.harness.add_relation("redis-cache", "redis-cache")
        self.harness.add_relation_unit(cache_relation_id, "redis-cache/0")

        cache_relation = self.harness.model.get_relation("redis-cache", cache_relation_id)
        cache_unit = self.harness.model.get_unit("redis-cache/0")
        cache_relation.data = {cache_unit: {"hostname": "cache-host", "port": 1011}}

        broker_relation = self.harness.model.get_relation("redis-broker", broker_relation_id)
        broker_unit = self.harness.model.get_unit("redis-broker/0")
        broker_relation.data = {broker_unit: {"hostname": "broker-host", "port": 1010}}

        self.nginx_route_relation_id = self.harness.add_relation(  # pylint: disable=W0201
            "nginx-route", "ingress"
        )
        self.harness.add_relation_unit(self.nginx_route_relation_id, "ingress/0")

    def is_ready(self, apps: List[str]):
        """Waiting for all applications to be ready.

        Args:
            apps: List of applications.
        """
        for app_name in apps:
            self.harness.container_pebble_ready(app_name)

    def set_relations_and_leader(self):
        """Set Indico relations, the leader and check container readiness."""
        self.set_up_all_relations()
        self.harness.set_leader(True)
        self.is_ready(
            [
                "indico",
                "indico-celery",
                "indico-nginx",
            ]
        )
