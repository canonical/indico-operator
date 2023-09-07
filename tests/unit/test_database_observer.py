# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Database observer unit tests."""

import ops
from ops.testing import Harness

from database_observer import DatabaseObserver

REQUIRER_METADATA = """
name: observer-charm
requires:
  database:
    interface: postgresql_client
"""


class ObservedCharm(ops.CharmBase):
    """Class for requirer charm testing."""

    def __init__(self, *args):
        """Init method for the class.

        Args:
            args: Variable list of positional arguments passed to the parent constructor.
        """
        super().__init__(*args)
        self.database = DatabaseObserver(self)
        self.events = []
        self.framework.observe(self.on.config_changed, self._record_event)

    def _record_event(self, event: ops.EventBase) -> None:
        """Rececord emitted event in the event list.

        Args:
            event: event.
        """
        self.events.append(event)


def test_database_created_emits_config_changed_event():
    """
    arrange: set up a charm and a database relation.
    act: trigger a database created event.
    assert: a config change event is emitted.
    """
    harness = Harness(ObservedCharm, meta=REQUIRER_METADATA)
    harness.begin()
    relation_id = harness.add_relation("database", "database-provider")
    harness.add_relation_unit(relation_id, "database-provider/0")
    relation = harness.charm.framework.model.get_relation("database", 0)
    harness.charm.database.database.on.database_created.emit(relation)
    assert len(harness.charm.events) == 1


def test_endpoints_changed_emits_config_changed_event():
    """
    arrange: set up a charm and a database relation.
    act: trigger a endpoints changed event.
    assert: a config change event is emitted.
    """
    harness = Harness(ObservedCharm, meta=REQUIRER_METADATA)
    harness.begin()
    relation_id = harness.add_relation("database", "database-provider")
    harness.add_relation_unit(relation_id, "database-provider/0")
    relation = harness.charm.framework.model.get_relation("database", 0)
    harness.charm.database.database.on.endpoints_changed.emit(relation)
    assert len(harness.charm.events) == 1


def test_uri():
    """
    arrange: set up a charm and a database relation with a populated databag.
    act: retrieve the uri.
    assert: the uri matches the databag content.
    """
    harness = Harness(ObservedCharm, meta=REQUIRER_METADATA)
    harness.begin()
    relation_id = harness.add_relation("database", "database-provider")
    harness.add_relation_unit(relation_id, "database-provider/0")
    harness.update_relation_data(
        relation_id,
        "database-provider",
        {
            "database": "indico",
            "endpoints": "postgresql-k8s-primary.local:5432",
            "password": "somepass",
            "username": "user1",
        },
    )
    assert harness.charm.database.uri == (
        "postgresql://user1:somepass@postgresql-k8s-primary.local:5432/indico"
    )


def test_uri_when_no_relation_data():
    """
    arrange: set up a charm and a database relation with an empty databag.
    act: retrieve the uri.
    assert: the uri is None.
    """
    harness = Harness(ObservedCharm, meta=REQUIRER_METADATA)
    harness.begin()
    relation_id = harness.add_relation("database", "database-provider")
    harness.add_relation_unit(relation_id, "database-provider/0")
    assert harness.charm.database.uri is None
