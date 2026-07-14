# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

# Learn more about testing at: https://ops.readthedocs.io/en/latest/explanation/testing.html

"""Unit tests for the Indico charm actions."""

from secrets import token_hex
from unittest.mock import patch

import ops
import ops.testing
import pytest

from charm import INDICO_WRAPPER, IndicoCharm

from .charm_metadata import CHARM_ACTIONS, CHARM_CONFIG, CHARM_META


@pytest.fixture(name="context")
def context_fixture() -> ops.testing.Context:
    """Build a Scenario context for the Indico charm."""
    return ops.testing.Context(
        charm_type=IndicoCharm,
        meta=CHARM_META,
        actions=CHARM_ACTIONS,
        config=CHARM_CONFIG,
    )


@pytest.fixture(name="peer")
def peer_fixture() -> ops.testing.PeerRelation:
    """An initialized secret-storage peer relation."""
    return ops.testing.PeerRelation(
        endpoint="secret-storage",
        local_app_data={"flask_secret_key": "test-secret-key"},
    )


@patch.object(IndicoCharm, "_gen_environment", return_value={})
def test_add_admin_success(
    _mock_env, context: ops.testing.Context, peer: ops.testing.PeerRelation
) -> None:
    """arrange: A container that returns a successful autocreate execution.
    act: Run the add-admin action.
    assert: The action reports the created user and the command output.
    """
    email = f"{token_hex(4)}@example.com"
    password = token_hex(8)
    mock_exec = ops.testing.Exec(
        command_prefix=[INDICO_WRAPPER, "indico", "autocreate", "admin"],
        return_code=0,
        stdout="Created admin",
    )
    container = ops.testing.Container(
        name="flask-app", can_connect=True, execs={mock_exec}
    )
    state_in = ops.testing.State(leader=True, containers={container}, relations={peer})

    context.run(
        context.on.action("add-admin", params={"email": email, "password": password}),
        state_in,
    )

    assert context.action_results is not None
    assert context.action_results["user"] == email
    assert context.action_results["output"] == "Created admin"


@patch.object(IndicoCharm, "_gen_environment", return_value={})
def test_add_admin_exec_error(
    _mock_env, context: ops.testing.Context, peer: ops.testing.PeerRelation
) -> None:
    """arrange: A container whose autocreate execution fails.
    act: Run the add-admin action.
    assert: The action fails with the workload error.
    """
    email = f"{token_hex(4)}@example.com"
    mock_exec = ops.testing.Exec(
        command_prefix=[INDICO_WRAPPER, "indico", "autocreate", "admin"],
        return_code=1,
        stdout="boom",
    )
    container = ops.testing.Container(
        name="flask-app", can_connect=True, execs={mock_exec}
    )
    state_in = ops.testing.State(leader=True, containers={container}, relations={peer})

    with pytest.raises(ops.testing.ActionFailed) as exc:
        context.run(
            context.on.action("add-admin", params={"email": email, "password": "pw"}),
            state_in,
        )

    assert f"Failed to create admin {email}" in exc.value.message


def test_add_admin_container_not_ready(
    context: ops.testing.Context, peer: ops.testing.PeerRelation
) -> None:
    """arrange: A container that cannot connect.
    act: Run the add-admin action.
    assert: The action fails because the workload container is unavailable.
    """
    container = ops.testing.Container(name="flask-app", can_connect=False)
    state_in = ops.testing.State(leader=True, containers={container}, relations={peer})

    with pytest.raises(ops.testing.ActionFailed) as exc:
        context.run(
            context.on.action(
                "add-admin", params={"email": "a@example.com", "password": "pw"}
            ),
            state_in,
        )

    assert "Cannot connect to the Indico workload container" in exc.value.message


@patch.object(IndicoCharm, "_gen_environment", return_value={})
def test_anonymize_user_success(
    _mock_env, context: ops.testing.Context, peer: ops.testing.PeerRelation
) -> None:
    """arrange: A container that returns a successful anonymize execution.
    act: Run the anonymize-user action with two emails.
    assert: The action reports the anonymized emails.
    """
    emails = "a@example.com,b@example.com"
    mock_exec = ops.testing.Exec(
        command_prefix=[INDICO_WRAPPER, "indico", "anonymize", "user"],
        return_code=0,
        stdout="anonymized",
    )
    container = ops.testing.Container(
        name="flask-app", can_connect=True, execs={mock_exec}
    )
    state_in = ops.testing.State(leader=True, containers={container}, relations={peer})

    context.run(
        context.on.action("anonymize-user", params={"email": emails}),
        state_in,
    )

    assert context.action_results is not None
    assert context.action_results["user"] == emails


@patch.object(IndicoCharm, "_gen_environment", return_value={})
def test_anonymize_user_exec_error(
    _mock_env, context: ops.testing.Context, peer: ops.testing.PeerRelation
) -> None:
    """arrange: A container whose anonymize execution fails.
    act: Run the anonymize-user action.
    assert: The action fails and the per-email failure is reported in the output.
    """
    email = "a@example.com"
    mock_exec = ops.testing.Exec(
        command_prefix=[INDICO_WRAPPER, "indico", "anonymize", "user"],
        return_code=1,
        stdout="boom",
    )
    container = ops.testing.Container(
        name="flask-app", can_connect=True, execs={mock_exec}
    )
    state_in = ops.testing.State(leader=True, containers={container}, relations={peer})

    with pytest.raises(ops.testing.ActionFailed) as exc:
        context.run(
            context.on.action("anonymize-user", params={"email": email}),
            state_in,
        )

    assert "Failed to anonymize one or more users" in exc.value.message


def test_anonymize_user_container_not_ready(
    context: ops.testing.Context, peer: ops.testing.PeerRelation
) -> None:
    """arrange: A container that cannot connect.
    act: Run the anonymize-user action.
    assert: The action fails because the workload container is unavailable.
    """
    container = ops.testing.Container(name="flask-app", can_connect=False)
    state_in = ops.testing.State(leader=True, containers={container}, relations={peer})

    with pytest.raises(ops.testing.ActionFailed) as exc:
        context.run(
            context.on.action("anonymize-user", params={"email": "a@example.com"}),
            state_in,
        )

    assert "Cannot connect to the Indico workload container" in exc.value.message


@patch.object(IndicoCharm, "_gen_environment", return_value={})
def test_anonymize_user_too_many_emails(
    _mock_env, context: ops.testing.Context, peer: ops.testing.PeerRelation
) -> None:
    """arrange: An email list longer than the allowed maximum.
    act: Run the anonymize-user action.
    assert: The action fails because too many emails were supplied.
    """
    emails = ",".join(f"user{i}@example.com" for i in range(51))
    container = ops.testing.Container(name="flask-app", can_connect=True)
    state_in = ops.testing.State(leader=True, containers={container}, relations={peer})

    with pytest.raises(ops.testing.ActionFailed) as exc:
        context.run(
            context.on.action("anonymize-user", params={"email": emails}),
            state_in,
        )

    assert "more than 50 emails not allowed" in exc.value.message


def test_refresh_external_resources(
    context: ops.testing.Context, peer: ops.testing.PeerRelation
) -> None:
    """arrange: A container that accepts the marker removal command.
    act: Run the refresh-external-resources action.
    assert: The action reports that a refresh was triggered.
    """
    mock_exec = ops.testing.Exec(
        command_prefix=["rm", "-f", "/srv/indico/plugins/.installed"],
        return_code=0,
    )
    container = ops.testing.Container(
        name="flask-app", can_connect=True, execs={mock_exec}
    )
    state_in = ops.testing.State(leader=True, containers={container}, relations={peer})

    with patch.object(IndicoCharm, "restart"):
        context.run(
            context.on.action("refresh-external-resources"),
            state_in,
        )

    assert context.action_results is not None
    assert context.action_results["result"] == "external plugins refresh triggered"


def test_refresh_external_resources_container_not_ready(
    context: ops.testing.Context, peer: ops.testing.PeerRelation
) -> None:
    """arrange: A container that cannot connect.
    act: Run the refresh-external-resources action.
    assert: The action fails because the workload container is unavailable.
    """
    container = ops.testing.Container(name="flask-app", can_connect=False)
    state_in = ops.testing.State(leader=True, containers={container}, relations={peer})

    with pytest.raises(ops.testing.ActionFailed) as exc:
        context.run(
            context.on.action("refresh-external-resources"),
            state_in,
        )

    assert "Cannot connect to the Indico workload container" in exc.value.message
