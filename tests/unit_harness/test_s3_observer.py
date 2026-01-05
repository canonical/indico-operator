# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""S3 observer unit tests."""

# pylint: disable=duplicate-code

from secrets import token_hex

import ops
from ops.testing import Harness

from s3_observer import S3Observer
from state import State

REQUIRER_METADATA = """
name: observer-charm
requires:
  s3:
    interface: s3
"""


class ObservedCharm(ops.CharmBase):
    """Class for requirer charm testing."""

    def __init__(self, *args):
        """Construct.

        Args:
            args: Variable list of positional arguments passed to the parent constructor.
        """
        super().__init__(*args)
        self.s3 = S3Observer(self)
        self.state = State.from_charm(charm=self)
        self.events = []
        self.framework.observe(self.on.config_changed, self._record_event)

    def _record_event(self, event: ops.EventBase) -> None:
        """Rececord emitted event in the event list.

        Args:
            event: event.
        """
        self.events.append(event)


def test_credentials_changed_emits_config_changed_event_and_updates_charm_state():
    """
    arrange: set up a charm.
    act: integrate with S3.
    assert: a config change event is emitted.
    """
    relation_data = {
        "bucket": "some-bucket",
        "host": "example.s3",
        "access-key": token_hex(16),
        "secret-key": token_hex(16),
    }
    harness = Harness(ObservedCharm, meta=REQUIRER_METADATA)
    harness.begin()
    harness.add_relation("s3", "s3-integrator", app_data=relation_data)
    assert len(harness.charm.events) == 1


def test_credentials_gone_emits_config_changed_event_and_updates_charm_state():
    """
    arrange: set up a charm and a s3 relation.
    act: remove the S3 relation.
    assert: a config change event is emitted.
    """
    relation_data = {
        "bucket": "some-bucket",
        "host": "example.s3",
        "access-key": token_hex(16),
        "secret-key": token_hex(16),
    }
    harness = Harness(ObservedCharm, meta=REQUIRER_METADATA)
    harness.begin()
    relation_id = harness.add_relation("s3", "s3-integrator", app_data=relation_data)
    harness.remove_relation(relation_id)
    assert len(harness.charm.events) == 2
