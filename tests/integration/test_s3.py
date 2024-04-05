#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Indico S3 integration tests."""

import json

import juju
import pytest
from ops import Application


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
@pytest.mark.usefixtures("s3_integrator")
async def test_s3(app: Application, s3_integrator: Application):
    """
    arrange: given charm integrated with S3.
    act: do nothing.
    assert: the pebble plan matches the S3 values as configured by the integrator.
    """
    # Application actually does have units
    indico_container = app.units[0].get_container("indico")  # type: ignore
    indico_env = indico_container.get_plan().services["indico"].environment
    storage_config = json.loads(indico_env["STORAGE_DICT"])
    # Application actually does have units
    action: juju.action.Action = await s3_integrator.units[0].run_action(  # type: ignore
        "get-s3-connection-info"
    )
    await action.wait()
    assert action.status == "completed"
    assert storage_config["s3"] == (
        f"s3:bucket={action.results['bucket']},host={action.results['endpoint']},"
        f"access_key={action.results['access-key']},secret_key={action.results['secret-key']},"
        "proxy=true"
    )
