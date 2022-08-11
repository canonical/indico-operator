#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

import pytest
import requests
from ops.model import ActiveStatus, Application
from pytest_operator.plugin import OpsTest


async def juju_run(unit, cmd):
    """Helper function that runs a juju command."""
    action = await unit.run(cmd)
    result = await action.wait()
    code = result["return-code"]
    stdout = result.get("stdout")
    stderr = result.get("stderr")
    assert code == "0", f"{cmd} failed ({code}): {stderr or stdout}"
    return stdout


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_active(ops_test: OpsTest, app: Application):
    """Check that the charm is active.

    Assume that the charm has already been built and is running.
    """
    assert app.units[0].workload_status == ActiveStatus.name


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_indico_is_up(ops_test: OpsTest, app: Application):
    """Check that the bootstrap page is reachable.

    Assume that the charm has already been built and is running.
    """
    # Read the IP address of indico
    status = await ops_test.model.get_status()
    unit = list(status.applications[app.name].units)[0]
    address = status["applications"][app.name]["units"][unit]["address"]
    # Send request to bootstrap page and set Host header to app_name (which the application
    # expects)
    response = requests.get(f"http://{address}:8080/bootstrap", headers={"Host": app.name})
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_health_checks(ops_test: OpsTest, app: Application):
    """Runs health checks for each container.

    Assume that the charm has already been built and is running.
    """
    unit = ops_test.model.applications[app.name].units[0]
    container_list = ["indico", "indico-nginx", "indico-celery"]
    for container in container_list:
        result = await juju_run(
            unit,
            f"PEBBLE_SOCKET=/charm/containers/{container}/pebble.socket /charm/bin/pebble checks",
        )

    if container != "indico-nginx":
        assert result.count("0/3") == 1
    else:
        assert result.count("0/3") == 2
