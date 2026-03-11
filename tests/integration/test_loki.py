#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Indico Loki integration tests."""

import logging
import time

import jubilant
import pytest
import requests

logger = logging.getLogger(__name__)


@pytest.mark.abort_on_fail
def test_loki(juju: jubilant.Juju, loki: str):
    """
    arrange: given charm integrated with Loki.
    act: do nothing.
    assert: Loki starts to receive log files from indico.
    """
    status = juju.status()
    loki_unit = list(status.apps[loki].units.values())[0]
    loki_ip = loki_unit.address
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
            time.sleep(1)
        if all(
            file in logged_files
            for file in ["/srv/indico/log/celery.log", "/srv/indico/log/indico.log"]
        ):
            return
    raise TimeoutError(f"Loki did not receive all log files from indico, received {logged_files}")
