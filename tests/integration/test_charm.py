#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Integration tests for the Indico charm."""

import logging
from secrets import token_hex

import jubilant
import pytest
import requests

logger = logging.getLogger(__name__)


@pytest.mark.abort_on_fail
def test_active(app: str, juju: jubilant.Juju):
    """Check that the charm is active after deployment.

    arrange: The charm has been built and deployed with postgresql and redis.
    act: Get the Juju status.
    assert: The indico, postgresql-k8s and redis-k8s units are active.
    """
    status = juju.status()
    assert status.apps[app].units[app + "/0"].is_active
    assert status.apps["postgresql-k8s"].units["postgresql-k8s/0"].is_active
    assert status.apps["redis-k8s"].units["redis-k8s/0"].is_active


@pytest.mark.abort_on_fail
def test_workload_online(indico_address: str, juju: jubilant.Juju):
    """Check that the Indico workload is responding to HTTP requests.

    arrange: The charm has been deployed and is active.
    act: Send an HTTP request to the Indico unit.
    assert: The response contains 'Indico'.
    """

    def is_indico_up(status):
        """Return True when all apps are active and Indico HTTP responds 200."""
        if not jubilant.all_active(status):
            return False
        try:
            return requests.get(indico_address, timeout=10).status_code == 200
        except requests.ConnectionError:
            return False

    juju.wait(is_indico_up)
    response = requests.get(indico_address, timeout=10)
    assert response.status_code == 200
    assert "Indico" in response.text


def test_add_admin_action(app: str, juju: jubilant.Juju) -> None:
    """Check that the add-admin action executes end-to-end.

    arrange: The charm is deployed and active.
    act: Run the add-admin action with a new email and password.
    assert: The action succeeds and reports the created user.
    """
    unit_name = f"{app}/0"
    email = f"{token_hex(4)}@example.com"
    task = juju.run(unit_name, "add-admin", {"email": email, "password": token_hex(8)})
    assert task.results["user"] == email


@pytest.mark.abort_on_fail
def test_ingress(app: str, juju: jubilant.Juju):
    """Check that integrating traefik-k8s provides a reachable ingress URL.

    arrange: The charm is deployed and active with postgresql and redis.
    act: Deploy traefik-k8s with subdomain routing, integrate with indico.
    assert: The ingress URL from the relation data is reachable and serves Indico.
    """
    # The base/s3/saml tests pin `site_url` to the pod address so Indico serves
    # over direct HTTP. Indico's BASE_URL prefers `site_url` over the ingress
    # URL, so it must be cleared here for requests routed through traefik
    # (Host: <model>-<app>.testing.local) to match.
    juju.config(app, reset="site_url")

    juju.deploy(
        "traefik-k8s",
        channel="latest/stable",
        trust=True,
        config={
            "routing_mode": "subdomain",
            "external_hostname": "testing.local",
        },
    )
    juju.wait(
        lambda status: jubilant.all_active(status, "traefik-k8s"),
        timeout=1200,
    )

    juju.integrate(f"{app}:ingress", "traefik-k8s:ingress")
    juju.wait(jubilant.all_active, timeout=1200)

    status = juju.status()
    traefik_unit_address = status.apps["traefik-k8s"].units["traefik-k8s/0"].address

    model = juju.model
    ingress_host = f"{model}-{app}.testing.local"
    logger.info("Ingress host: %s, traefik address: %s", ingress_host, traefik_unit_address)

    def ingress_reachable(status):
        if not jubilant.all_active(status):
            return False
        try:
            resp = requests.get(
                f"http://{traefik_unit_address}",
                headers={"Host": ingress_host},
                timeout=10,
            )
            return resp.status_code == 200
        except (requests.ConnectionError, requests.Timeout):
            return False

    juju.wait(ingress_reachable, timeout=300)

    response = requests.get(
        f"http://{traefik_unit_address}",
        headers={"Host": ingress_host},
        timeout=10,
    )
    assert response.status_code == 200
    assert "Indico" in response.text
