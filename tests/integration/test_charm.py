#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Indico charm integration tests."""

import logging

import jubilant
import pytest
import requests

from charm import CELERY_PROMEXP_PORT, NGINX_PROMEXP_PORT, STATSD_PROMEXP_PORT

ADMIN_USER_EMAIL = "sample@email.com"
ADMIN_USER_EMAIL_FAIL = "sample2@email.com"

logger = logging.getLogger()


@pytest.mark.abort_on_fail
def test_active(juju: jubilant.Juju, app: str):
    """Check that the charm is active.

    Assume that the charm has already been built and is running.
    """
    status = juju.status()
    assert status.apps[app].app_status.current == "active"


@pytest.mark.abort_on_fail
def test_indico_is_up(juju: jubilant.Juju, app: str):
    """Check that the bootstrap page is reachable.

    Assume that the charm has already been built and is running.
    """
    status = juju.status()
    unit_status = list(status.apps[app].units.values())[0]
    address = unit_status.address
    response = requests.get(
        f"http://{address}:8080/bootstrap", headers={"Host": f"{app}.local"}, timeout=10
    )
    assert response.status_code == 200


@pytest.mark.abort_on_fail
def test_health_checks(juju: jubilant.Juju, app: str):
    """Runs health checks for each container.

    Assume that the charm has already been built and is running.
    """
    container_checks_list = [("indico-nginx", 2), ("indico", 4)]
    for container, expected_count in container_checks_list:
        cmd = (
            f"PEBBLE_SOCKET=/charm/containers/{container}/pebble.socket"
            " /charm/bin/pebble checks"
        )
        stdout = juju.cli("exec", "--unit", f"{app}/0", "--", "bash", "-c", cmd)
        # When executing the checks, `0/3` means there are 0 errors of 3.
        # Each check has its own `0/3`, so we count `n` times where `n` is the
        # number of checks for that container.
        assert stdout.count("0/3") == expected_count


@pytest.mark.abort_on_fail
def test_prom_exporters_are_up(juju: jubilant.Juju, app: str):
    """
    arrange: given charm in its initial state
    act: when the metrics endpoints are scraped
    assert: the response is 200 (HTTP OK)
    """
    prometheus_targets = [
        f"localhost:{NGINX_PROMEXP_PORT}",
        f"localhost:{STATSD_PROMEXP_PORT}",
        f"localhost:{CELERY_PROMEXP_PORT}",
    ]
    for target in prometheus_targets:
        cmd = f"curl -f -m 10 http://{target}/metrics"
        # CLIError is raised if the command fails, so a successful return means status 200.
        juju.cli("exec", "--unit", f"{app}/0", "--", "bash", "-c", cmd)
