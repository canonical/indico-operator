#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Indico Loki integration tests."""
import asyncio
import json
import logging
import time

import pytest
import requests
from juju.application import Application
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_loki(loki: Application, ops_test: OpsTest):
    """
    arrange: given charm integrated with Loki.
    act: do nothing.
    assert: Loki starts to receive log files from indico.
    """
    _, status, _ = await ops_test.juju("status", "--format", "json")
    status = json.loads(status)
    loki_ip = next(status["applications"][loki.name]["units"].values())["address"]
    logger.info("loki IP: %s", loki_ip)
    deadline = time.time() + 1200
    logged_files = []
    while time.time() < deadline:
        try:
            logged_files = (
                requests.get(
                    f"http://{loki_ip}:3100/loki/api/v1/label/filename/values",
                    timeout=10,
                )
                .json()
                .get("data", [])
            )
        except (requests.exceptions.RequestException, TimeoutError):
            await asyncio.sleep(1)
        if all(
            file in logged_files
            for file in ["/srv/indico/log/celery.log", "/srv/indico/log/indico.log"]
        ):
            return
    raise TimeoutError(f"Loki did not receive all log files from indico, received {logged_files}")
