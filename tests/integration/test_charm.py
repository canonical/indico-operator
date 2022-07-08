#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.


import logging
from pathlib import Path

import pytest
import yaml
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)

METADATA = yaml.safe_load(Path("./metadata.yaml").read_text())
APP_NAME = METADATA["name"]

async def juju_run(unit, cmd):
    """Helper function that runs a juju command"""
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
    await ops_test.model.deploy("redis-k8s")
    await ops_test.model.deploy(charm, resources=resources, application_name=APP_NAME)
    await ops_test.model.wait_for_idle()
    assert ops_test.model.applications[APP_NAME].units[0].workload_status == "waiting"
    await ops_test.model.add_relation(APP_NAME, "postgresql-k8s:db")
    await ops_test.model.add_relation(APP_NAME, "redis-k8s")
    await ops_test.model.wait_for_idle()
    assert ops_test.model.applications[APP_NAME].units[0].workload_status == "active"

@pytest.mark.abort_on_fail
async def test_health_checks(ops_test: OpsTest):
    contlist = ["indico", "indico-nginx", "indico-celery"]
    app = ops_test.model.applications["indico"]
    indico_unit = app.units[0]
    for cont in contlist:
        req = await juju_run(indico_unit, 'PEBBLE_SOCKET=/charm/containers/{}/pebble.socket /charm/bin/pebble checks'.format(cont))
        if cont != "indico-nginx":
            assert req.count("0/3") == 1
        else:
            assert req.count("0/3") == 2
    
    
  