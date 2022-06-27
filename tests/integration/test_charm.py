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
    await ops_test.model.deploy("redis-k8s")
    await ops_test.model.deploy("postgresql-k8s")
    await ops_test.model.deploy(charm, resources=resources, application_name=APP_NAME)
    await ops_test.model.add_relation(APP_NAME, "redis-k8s")
    await ops_test.model.add_relation(APP_NAME, "postgresql-k8s:db")
    await ops_test.model.wait_for_idle(
        apps=[APP_NAME, "redis-k8s", "postgresql-k8s"], status="active"
    )
    assert ops_test.model.applications[APP_NAME].units[0].workload_status == "active"
