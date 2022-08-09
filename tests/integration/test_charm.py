#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.


import logging
from pathlib import Path

import pytest
import requests
import yaml
from ops.model import ActiveStatus
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)

METADATA = yaml.safe_load(Path("./metadata.yaml").read_text())
APP_NAME = METADATA["name"]


async def juju_run(unit, cmd):
    """Helper function that runs a juju command."""
    result = await unit.run(cmd)
    code = result.results["Code"]
    stdout = result.results.get("Stdout")
    stderr = result.results.get("Stderr")
    assert code == "0", f"{cmd} failed ({code}): {stderr or stdout}"
    return stdout


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_active(ops_test: OpsTest, app_name: str, indico_charm):
    """Check that the charm is active.

    Assume that the charm has already been built and is running.
    """
    assert ops_test.model.applications[app_name].units[0].workload_status == ActiveStatus.name


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_indico_is_up(ops_test: OpsTest, app_name: str, indico_charm):
    """Check that the bootstrap page is reachable.

    Assume that the charm has already been built and is running.
    """
    # Read the IP address of indico
    status = await ops_test.model.get_status()
    unit = list(status.applications[app_name].units)[0]
    address = status["applications"][app_name]["units"][unit]["address"]

    # Send request to bootstrap page and set Host header to app_name (which the application
    # expects)
    response = requests.get(f"http://{address}:8080/bootstrap", headers={"Host": app_name})
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_health_checks(ops_test: OpsTest, indico_charm):
    """Runs health checks for each container.

    Assume that the charm has already been built and is running.
    """
    container_list = ["indico", "indico-nginx", "indico-celery"]
    app = ops_test.model.applications["indico"]
    indico_unit = app.units[0]
    for container in container_list:
        result = await juju_run(
            indico_unit,
            f"PEBBLE_SOCKET=/charm/containers/{container}/pebble.socket /charm/bin/pebble checks",
        )
        # When executing the checks, `0/3` means there are 0 errors of 3.
        # Each check has it's own `0/3`, so we will count `n` times,
        # where `n` is the number of checks for that container.
        if container != "indico-nginx":
            assert result.count("0/3") == 1
        else:
            assert result.count("0/3") == 2
