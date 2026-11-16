# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

# Learn more about testing at: https://ops.readthedocs.io/en/latest/explanation/testing.html

"""Unit tests for the Indico charm base behaviour."""

from unittest.mock import MagicMock

import ops
import ops.testing
import pytest
from paas_charm.redis import PaaSRedisRelationData, PaaSRedisRequires
from paas_charm.valkey import ValkeyClientRequirer

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


def _ready_state() -> ops.testing.State:
    """Build a state with the container, peer and postgresql relations ready."""
    container = ops.testing.Container(name="flask-app", can_connect=True)
    peer = ops.testing.PeerRelation(
        endpoint="secret-storage",
        local_app_data={"flask_secret_key": "test-secret-key"},
    )
    postgresql = ops.testing.Relation(
        endpoint="postgresql",
        remote_app_data={
            "database": "indico",
            "endpoints": "postgresql:5432",
            "username": "user",
            "password": "pass",
        },
    )
    return ops.testing.State(
        leader=True,
        containers={container},
        relations={peer, postgresql},
    )


def _patch_cache_backends(monkeypatch: pytest.MonkeyPatch, valkey: bool, redis: bool) -> None:
    """Patch the valkey and redis requirers to report whether they are ready."""
    monkeypatch.setattr(
        ValkeyClientRequirer,
        "to_relation_data",
        lambda _: (
            MagicMock(endpoints="valkey:6379", username=None, password=None) if valkey else None
        ),
    )
    monkeypatch.setattr(
        PaaSRedisRequires,
        "to_relation_data",
        lambda _: PaaSRedisRelationData(url="redis://redis:6379") if redis else None,
    )


def test_missing_valkey_and_redis_integrations(monkeypatch):
    """arrange: State with postgresql ready but neither valkey nor redis integrated.
    act: Run pebble_ready hook.
    assert: The unit is blocked asking for valkey or redis.
    """
    _patch_cache_backends(monkeypatch, valkey=False, redis=False)
    context = _context()
    state_in = _ready_state()

    state_out = context.run(context.on.pebble_ready(state_in.get_container("flask-app")), state_in)

    assert state_out.unit_status == ops.testing.BlockedStatus(
        "missing integrations: valkey or redis"
    )


def test_both_valkey_and_redis_integrations(monkeypatch):
    """arrange: State with postgresql, valkey and redis integrated.
    act: Run pebble_ready hook.
    assert: The unit is blocked because only one cache backend is supported.
    """
    _patch_cache_backends(monkeypatch, valkey=True, redis=True)
    context = _context()
    state_in = _ready_state()

    state_out = context.run(context.on.pebble_ready(state_in.get_container("flask-app")), state_in)

    assert state_out.unit_status == ops.testing.BlockedStatus(
        "Only one of valkey or redis integrations is supported"
    )


@pytest.mark.parametrize(
    "valkey, redis",
    [
        pytest.param(True, False, id="valkey"),
        pytest.param(False, True, id="redis"),
    ],
)
def test_single_cache_integration(monkeypatch, valkey, redis):
    """arrange: State with postgresql and exactly one of valkey or redis integrated.
    act: Check whether the charm is ready.
    assert: The charm is ready to start the workload.
    """
    _patch_cache_backends(monkeypatch, valkey=valkey, redis=redis)
    context = _context()

    with context(context.on.update_status(), _ready_state()) as manager:
        assert manager.charm.is_ready()
