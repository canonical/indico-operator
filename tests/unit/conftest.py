# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

import pytest
from ops import pebble, testing


@pytest.fixture(scope="function", name="base_state")
def base_state_fixture():
    """State with container and config file set."""
    pebble_layer = pebble.Layer(
        {
            "summary": "indico layer",
            "description": "pebble config layer for indico",
            "services": {
                "indico": {},
            },
        }
    )
    yield {
        "leader": True,
        "containers": {
            # mypy throws an error because it validates against ops.Container.
            testing.Container(  # type: ignore[call-arg]
                name="indico",
                can_connect=True,
                layers={"indico": pebble_layer},
                service_statuses={"indico": pebble.ServiceStatus.ACTIVE},
            )
        },
    }
