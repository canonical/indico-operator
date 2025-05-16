# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Indico charm unit tests."""

from unittest.mock import MagicMock, patch

import ops
from ops import testing

from charm import IndicoOperatorCharm


@patch.object(ops.JujuVersion, "from_environ")
def test_on_leader_elected_when_secrets_supported(mock_juju_env, base_state: dict):
    """
    arrange: charm created, leader selected and secrets supported
    act: re-trigger the leader elected event
    assert: the peer relation containers the secret-key
    """
    mock_juju_env.return_value = MagicMock(has_secrets=True)
    base_state["relations"] = [testing.PeerRelation("indico-peers")]
    state = testing.State(**base_state)
    context = testing.Context(
        charm_type=IndicoOperatorCharm,
    )

    state = context.run(context.on.leader_elected(), state)

    print(state.get_relations("indico-peers"))
    secret_id = state.get_relations("indico-peers")[0].local_app_data["secret-id"]
    context.run(context.on.leader_elected(), state)

    assert secret_id == state.get_relations("indico-peers")[0].local_app_data["secret-id"]
