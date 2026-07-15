#!/usr/bin/env python3

# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""SMTP integration tests for the Indico charm."""

import logging

import jubilant
import pytest

from .conftest import JUJU_WAIT_TIMEOUT

logger = logging.getLogger(__name__)

# Non-routable RFC 5737 TEST-NET-1 address — smtp-integrator becomes active
# without needing a real SMTP server.
_SMTP_HOST = "192.0.2.1"
_SMTP_PORT = 587
_SMTP_DOMAIN = "test.example.com"


@pytest.mark.abort_on_fail
def test_smtp_integration(app: str, juju: jubilant.Juju):
    """Check that smtp-integrator passes SMTP env vars to the workload correctly.

    arrange: The charm is deployed and active with postgresql and redis.
    act: Deploy smtp-integrator, configure it, and integrate with indico.
    assert: The charm remains active and the pebble plan for the workload
        service contains the SMTP_HOST and SMTP_PORT env vars set by paas-charm
        from the smtp relation data.
    """
    juju.deploy(
        "smtp-integrator",
        channel="latest/stable",
        config={
            "host": _SMTP_HOST,
            "port": _SMTP_PORT,
            "domain": _SMTP_DOMAIN,
            "transport_security": "none",
            "auth_type": "none",
        },
    )
    juju.wait(
        lambda status: jubilant.all_active(status, "smtp-integrator"),
        timeout=JUJU_WAIT_TIMEOUT,
    )

    # Integrate explicitly on the modern `smtp` interface (not smtp-legacy).
    juju.integrate(f"{app}:smtp", "smtp-integrator:smtp")
    juju.wait(jubilant.all_active, timeout=JUJU_WAIT_TIMEOUT)
    logger.info("Indico is active after SMTP integration")

    # Verify via pebble plan — paas-charm writes SMTP_* env vars into the
    # workload pebble service layer; the charm container can read the plan
    # via the shared pebble socket.
    task = juju.exec(
        "PEBBLE_SOCKET=/charm/containers/flask-app/pebble.socket pebble plan",
        unit=f"{app}/0",
    )
    plan = task.stdout
    logger.info("Pebble plan:\n%s", plan)

    assert (
        f"SMTP_HOST: {_SMTP_HOST}" in plan
    ), f"Expected SMTP_HOST: {_SMTP_HOST} in pebble plan, got:\n{plan}"
    assert (
        str(_SMTP_PORT) in plan
    ), f"Expected SMTP_PORT {_SMTP_PORT} in pebble plan, got:\n{plan}"
