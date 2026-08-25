# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

# Learn more about testing at: https://ops.readthedocs.io/en/latest/explanation/testing.html

"""Unit tests for the Indico charm base behaviour."""

import ops
import ops.testing

from charm import IndicoCharm

from .charm_metadata import CHARM_ACTIONS, CHARM_CONFIG, CHARM_META


def _context() -> ops.testing.Context:
    """Build a Scenario context for the Indico charm."""
    return ops.testing.Context(
        charm_type=IndicoCharm,
        meta=CHARM_META,
        actions=CHARM_ACTIONS,
        config=CHARM_CONFIG,
    )


def test_container_not_ready():
    """arrange: State with the flask-app container that cannot connect.
    act: Run config_changed hook.
    assert: The unit is waiting for Pebble.
    """
    context = _context()
    container = ops.testing.Container(name="flask-app", can_connect=False)
    state_in = ops.testing.State(containers={container})

    state_out = context.run(context.on.config_changed(), state_in)

    assert state_out.unit_status == ops.testing.WaitingStatus(
        "Waiting for pebble ready"
    )


def test_missing_peer_relation():
    """arrange: State with the container ready but no peer relation.
    act: Run pebble_ready hook.
    assert: The unit is waiting for the peer integration.
    """
    context = _context()
    container = ops.testing.Container(name="flask-app", can_connect=True)
    state_in = ops.testing.State(containers={container})

    state_out = context.run(context.on.pebble_ready(container), state_in)

    assert state_out.unit_status == ops.testing.WaitingStatus(
        "Waiting for peer integration"
    )


def test_missing_database_integration():
    """arrange: State with the container ready and the peer relation, but no
        postgresql/redis integrations.
    act: Run pebble_ready hook.
    assert: The unit is blocked due to the missing mandatory integrations.
    """
    context = _context()
    container = ops.testing.Container(name="flask-app", can_connect=True)
    peer = ops.testing.PeerRelation(
        endpoint="secret-storage",
        local_app_data={"flask_secret_key": "test-secret-key"},
    )
    state_in = ops.testing.State(
        leader=True,
        containers={container},
        relations={peer},
    )

    state_out = context.run(context.on.pebble_ready(container), state_in)

    assert state_out.unit_status.name == "blocked"
