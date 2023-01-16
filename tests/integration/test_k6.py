#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Loading tests using k6."""

import os
import tempfile
from pathlib import Path

import docker
import pytest
from ops.model import Application
from pytest_operator.plugin import OpsTest


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_load(ops_test: OpsTest, app: Application):
    """Load test the charm.

    Assume that the charm has already been built and is running.
    """

    assert ops_test.model

    status = await ops_test.model.get_status()
    unit = list(status.applications[app.name].units)[0]
    indico_address = status["applications"][app.name]["units"][unit]["address"]

    tmpdir = tempfile.mkdtemp(dir=os.environ["TOX_WORK_DIR"])
    with open(
        Path("tests/integration/k6_script.js").resolve(), "r", encoding="utf-8"
    ) as k6_script:
        with open(tmpdir + "/script.js", "w", encoding="utf-8") as runnable_script:
            runnable_script.write(k6_script.read().format(target_ip=indico_address))

    os.chmod(tmpdir, 0o755)  # nosec
    os.chmod(tmpdir + "/script.js", 0o755)  # nosec
    client = docker.from_env()
    client.images.pull("grafana/k6", tag="0.42.0")
    logs = client.containers.run(
        image="grafana/k6",
        remove=True,
        command=["run", "/scripts/script.js"],
        volumes=[f"{tmpdir}:/scripts"],
    )
    print(logs.decode("utf-8"))
