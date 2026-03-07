#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Indico S3 integration tests."""

import re

import jubilant
import pytest
import yaml


@pytest.mark.abort_on_fail
@pytest.mark.usefixtures("s3_integrator")
def test_s3(juju: jubilant.Juju, app: str, s3_integrator: str):
    """
    arrange: given charm integrated with S3.
    act: do nothing.
    assert: the pebble plan matches the S3 values as configured by the integrator.
    """
    stdout = juju.cli("ssh", "--container", app, f"{app}/0", "pebble", "plan")
    plan = yaml.safe_load(stdout)
    indico_env = plan["services"]["indico"]["environment"]
    # STORAGE_DICT is a string representation of a Python dict
    # pylint: disable=eval-used
    storage_config = eval(indico_env["STORAGE_DICT"])  # nosec
    task = juju.run(f"{s3_integrator}/0", "get-s3-connection-info")
    assert task.success
    # in get-s3-connection-info, access_key and secret_key are redacted
    assert re.match(
        f"s3:bucket={task.results['bucket']},"
        f"access_key=[^=]+,secret_key=[^=]+,proxy=true,host={task.results['endpoint']}",
        storage_config["s3"],
    )
