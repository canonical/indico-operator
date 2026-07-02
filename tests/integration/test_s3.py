#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""S3 integration tests for the Indico charm."""

import logging

import jubilant
import pytest
import requests

from .conftest import JUJU_WAIT_TIMEOUT, generate_s3_config

logger = logging.getLogger(__name__)


def _indico_up(address: str) -> bool:
    """Return True when Indico responds with HTTP 200."""
    try:
        return requests.get(address, timeout=5).status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False


@pytest.mark.abort_on_fail
def test_s3_storage(
    app: str,
    juju: jubilant.Juju,
    indico_address: str,
    s3_address: str | None,
):
    """Check that Indico stays healthy when S3 storage is configured.

    arrange: The charm is deployed and active. An S3-compatible endpoint
        (e.g. MicroCeph radosgw / MinIO) is reachable at ``s3_address``.
    act: Deploy s3-integrator, configure it, sync credentials, and integrate
        with indico.
    assert: All applications become active and Indico keeps serving HTTP 200
        after the storage backend is switched to S3.
    """
    if not s3_address:
        pytest.skip("requires --s3-address argument or reachable host IP")
        return

    s3_conf = generate_s3_config(s3_address)

    juju.deploy(
        "s3-integrator",
        channel="latest/stable",
        config={
            "endpoint": s3_conf["endpoint"],
            "bucket": s3_conf["bucket"],
            "path": s3_conf["path"],
            "region": s3_conf["region"],
            "s3-uri-style": "path",
        },
    )
    juju.wait(lambda status: jubilant.all_blocked(status, "s3-integrator"))

    juju.run(
        "s3-integrator/0",
        "sync-s3-credentials",
        {
            "access-key": s3_conf["access-key"],
            "secret-key": s3_conf["secret-key"],
        },
    )
    juju.wait(lambda status: jubilant.all_active(status, "s3-integrator"))

    juju.integrate(app, "s3-integrator")

    def all_active_and_indico_serving(status):
        return jubilant.all_active(status) and _indico_up(indico_address)

    juju.wait(all_active_and_indico_serving, timeout=JUJU_WAIT_TIMEOUT)
    assert _indico_up(indico_address)

    # Cleanup: remove the s3-integrator relation
    juju.remove_relation(app, "s3-integrator")
    juju.wait(jubilant.all_active, timeout=JUJU_WAIT_TIMEOUT)
