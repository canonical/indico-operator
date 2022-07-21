#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.


import logging
from pathlib import Path

import pytest
import yaml
from ops.model import ActiveStatus, WaitingStatus
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


@pytest.mark.abort_on_fail
async def test_build_and_deploy(ops_test: OpsTest, indico_image, indico_nginx_image):
    """Build the charm-under-test and deploy it together with related charms.

    Assert on the unit status before any relations/configurations take place.
    """
    # build and deploy charm from local source folder
    charm = await ops_test.build_charm(".")
    resources = {
        "indico-image": indico_image,
        "indico-nginx-image": indico_nginx_image,
    }
    await ops_test.model.deploy("postgresql-k8s")
    await ops_test.model.deploy("redis-k8s", "redis-broker")
    await ops_test.model.deploy("redis-k8s", "redis-cache")
    await ops_test.model.deploy(charm, resources=resources, application_name=APP_NAME)
    await ops_test.model.wait_for_idle()
    assert ops_test.model.applications[APP_NAME].units[0].workload_status == WaitingStatus.name
    await ops_test.model.add_relation(APP_NAME, "postgresql-k8s:db")
    await ops_test.model.add_relation(APP_NAME, "redis-broker")
    await ops_test.model.add_relation(APP_NAME, "redis-cache")
    await ops_test.model.wait_for_idle(status="active")
    assert ops_test.model.applications[APP_NAME].units[0].workload_status == ActiveStatus.name


@pytest.mark.abort_on_fail
async def test_health_checks(ops_test: OpsTest):
    container_list = ["indico", "indico-nginx", "indico-celery"]
    app = ops_test.model.applications["indico"]
    indico_unit = app.units[0]
    for container in container_list:
        result = await juju_run(
            indico_unit,
            "PEBBLE_SOCKET=/charm/containers/{}/pebble.socket /charm/bin/pebble checks".format(
                container
            ),
        )
        # When executing the checks, `0/3` means there are 0 errors of 3.
        # Each check has it's own `0/3`, so we will count `n` times,
        # where `n` is the number of checks for that container.
        if container != "indico-nginx":
            assert result.count("0/3") == 1
        else:
            assert result.count("0/3") == 2
