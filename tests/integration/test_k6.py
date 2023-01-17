#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Loading tests using k6."""

import os
import re
import tempfile
from pathlib import Path

import docker
import pytest
from ops.model import Application
from pytest_operator.plugin import OpsTest

from tests.integration.helpers import get_unit_address


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_load(ops_test: OpsTest, app: Application):
    """Load test the charm.

    Assume that the charm has already been built and is running.
    """

    assert ops_test.model

    indico_address = await get_unit_address(ops_test, app.name)
    status = await ops_test.model.get_status()
    msg = status.applications["nginx-ingress-integrator"].status.info
    m = re.match(r"Ingress IP\(s\): ([\d\.]+), Service IP\(s\): ([\d\.]+)", msg)
    ip_address: str = m.group(1) if m and m.group(1) else ""

    assert ip_address

    tmpdir = tempfile.mkdtemp(dir=os.environ["TOX_WORK_DIR"])
    with open(
        Path("tests/integration/k6_script.js").resolve(), "r", encoding="utf-8"
    ) as k6_script:
        with open(tmpdir + "/script.js", "w", encoding="utf-8") as runnable_script:
            runnable_script.write(
                k6_script.read().replace("{", "{{").replace("}", "}}").format(target_ip=ip_address)
            )

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
