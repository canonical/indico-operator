# Copyright 2025 Canonical Ltd.
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
        # pylint: disable=duplicate-code
        self.harness.add_relation(
            "database",
            "postgresql",
            app_data={
                "database": "indico",
                "endpoints": "postgresql-k8s-primary.local:5432",
                "password": "somepass",
                "username": "user1",
            },
        )

        self.harness.add_relation("indico-peers", self.harness.charm.app.name)
        redis_broker_relation_id = self.harness.add_relation(
            "redis-broker",
            "redis-broker",
            unit_data={"hostname": "broker-host", "port": "1010"},
            app_data={"leader-host": "broker-host"},
        )
        self.harness.add_relation_unit(redis_broker_relation_id, "redis-broker/1")
        self.harness.update_relation_data(
            redis_broker_relation_id,
            "redis-broker/1",
            {"hostname": "broker-host-1", "port": "1010"},
        )
        redis_cache_relation_id = self.harness.add_relation(
            "redis-cache",
            "redis-cache",
            unit_data={"hostname": "cache-host", "port": "1011"},
            app_data={"leader-host": "cache-host"},
        )
        self.harness.add_relation_unit(redis_cache_relation_id, "redis-cache/1")
        self.harness.update_relation_data(
            redis_cache_relation_id,
            "redis-cache/1",
            {"hostname": "cache-host-1", "port": "1011"},
        )

        self.nginx_route_relation_id = self.harness.add_relation(  # pylint: disable=W0201
            "nginx-route", "ingress"
        )

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
                "indico-nginx",
            ]
        )
