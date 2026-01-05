# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""SAML observer unit tests."""

# pylint: disable=duplicate-code

import ops
from ops.testing import Harness

from saml_observer import SamlObserver
from state import State

REQUIRER_METADATA = """
name: observer-charm
requires:
  saml:
    interface: saml
"""


class ObservedCharm(ops.CharmBase):  # pylint: disable=duplicate-code
    """Class for requirer charm testing."""

    def __init__(self, *args):
        """Construct.

        Args:
            args: Variable list of positional arguments passed to the parent constructor.
        """
        super().__init__(*args)
        self.smtp = SamlObserver(self)
        self.state = State.from_charm(charm=self)
        self.events = []
        self.framework.observe(self.on.config_changed, self._record_event)

    def _record_event(self, event: ops.EventBase) -> None:
        """Rececord emitted event in the event list.

        Args:
            event: event.
        """
        self.events.append(event)


def test_saml_related_emits_config_changed_event_and_updates_charm_state():
    """
    arrange: set up a charm and a saml relation.
    act: trigger a relation changed event.
    assert: a config change event is emitted and the state, updated.
    """
    relation_data = {
        "entity_id": "https://login.staging.ubuntu.com",
        "metadata_url": "https://login.staging.ubuntu.com/saml/metadata",
        "x509certs": "cert1,cert2",
        "single_sign_on_service_redirect_url": "https://login.staging.ubuntu.com/saml/",
        "single_sign_on_service_redirect_binding": (
            "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        ),
        "single_logout_service_redirect_url": "https://login.staging.ubuntu.com/+logout",
        "single_logout_service_redirect_binding": (
            "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        ),
        "single_logout_service_redirect_response_url": "https://login.staging.ubuntu.com/+logout2",
    }
    harness = Harness(ObservedCharm, meta=REQUIRER_METADATA)
    harness.begin()
    harness.add_relation("saml", "saml", app_data=relation_data)
    assert len(harness.charm.events) == 1
