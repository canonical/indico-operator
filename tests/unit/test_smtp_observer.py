# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Database observer unit tests."""

import ops
from ops.testing import Harness

from smtp_observer import SmtpObserver
from state import State

REQUIRER_METADATA = """
name: observer-charm
requires:
  smtp-legacy:
    interface: saml
"""


class ObservedCharm(ops.CharmBase):
    """Class for requirer charm testing."""

    def __init__(self, *args):
        """Construct.

        Args:
            args: Variable list of positional arguments passed to the parent constructor.
        """
        super().__init__(*args)
        self.smtp = SmtpObserver(self)
        self.state = State.from_charm(self)
        self.events = []
        self.framework.observe(self.on.config_changed, self._record_event)

    def _record_event(self, event: ops.EventBase) -> None:
        """Rececord emitted event in the event list.

        Args:
            event: event.
        """
        self.events.append(event)


def test_smtp_related_emits_config_changed_eventand_updates_charm_state():
    """
    arrange: set up a charm and a smtp relation.
    act: trigger a relation changed event.
    assert: a config change event is emitted and the state, updated.
    """
    relation_data = {
        "host": "example.smtp",
        "port": "25",
        "user": "example_user",
        "password": "somepassword",  # nosec
        "auth_type": "plain",
        "transport_security": "tls",
        "domain": "domain",
    }
    harness = Harness(ObservedCharm, meta=REQUIRER_METADATA)
    harness.begin()
    relation_id = harness.add_relation("smtp-legacy", "smtp-integrator")
    harness.add_relation_unit(relation_id, "smtp-integrator/0")
    harness.update_relation_data(
        relation_id,
        "smtp-integrator",
        relation_data,
    )
    assert len(harness.charm.events) == 1
    assert harness.charm.smtp.smtp_config.host == relation_data["host"]
    assert harness.charm.smtp.smtp_config.port == int(relation_data["port"])
    assert harness.charm.smtp.smtp_config.login == relation_data["user"]
    assert harness.charm.smtp.smtp_config.password == relation_data["password"]
    assert harness.charm.smtp.smtp_config.use_tls
