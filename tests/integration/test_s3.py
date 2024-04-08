#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Indico S3 integration tests."""

import re

import juju
import pytest
import yaml
from ops import Application
from pytest_operator.plugin import OpsTest


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
@pytest.mark.usefixtures("s3_integrator")
async def test_s3(app: Application, s3_integrator: Application, ops_test: OpsTest):
    """
    arrange: given charm integrated with S3.
    act: do nothing.
    assert: the pebble plan matches the S3 values as configured by the integrator.
    """
    # Application actually does have units
    return_code, stdout, _ = await ops_test.juju(
        "ssh", "--container", app.name, app.units[0].name, "pebble", "plan"  # type: ignore
    )
    assert return_code == 0
    plan = yaml.safe_load(stdout)
    indico_env = plan["services"]["indico"]["environment"]
    # STORAGE_DICT is a string representation of a Python dict
    # pylint: disable=eval-used
    storage_config = eval(indico_env["STORAGE_DICT"])  # nosec
    # Application actually does have units
    action: juju.action.Action = await s3_integrator.units[0].run_action(  # type: ignore
        "get-s3-connection-info"
    )
    await action.wait()
    assert action.status == "completed"
    # in get-s3-connection-info, access_key and secret_key are redacted
    assert re.match(
        f"s3:bucket={action.results['bucket']},host={action.results['endpoint']},"
        f"access_key=[^=]+,secret_key=[^=]+,proxy=true",
        storage_config["s3"],
    )
