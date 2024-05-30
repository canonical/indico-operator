#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Indico Loki integration tests."""

import time

import pytest
import requests
from juju.application import Application
from juju.unit import Unit


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_loki(loki: Application):
    """
    arrange: given charm integrated with Loki.
    act: do nothing.
    assert: Loki starts to receive log files from indico.
    """
    loki_unit: Unit = loki.units[0]
    loki_ip = await loki_unit.get_public_address()
    deadline = time.time() + 600
    logged_files = []
    while time.time() < deadline:
        logged_files = (
            requests.get(
                f"http://{loki_ip}:3100/loki/api/v1/label/filename/values",
                timeout=10,
            )
            .json()
            .get("data", [])
        )
        if all(
            file in logged_files
            for file in ["/srv/indico/log/celery.log", "/srv/indico/log/indico.log"]
        ):
            return
    raise TimeoutError(f"Loki did not receive all log files from indico, received {logged_files}")
