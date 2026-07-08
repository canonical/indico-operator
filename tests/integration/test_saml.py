#!/usr/bin/env python3

# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""SAML integration tests for the Indico charm."""

import logging
from urllib.parse import urlparse

import jubilant
import pytest
import requests

from .conftest import JUJU_WAIT_TIMEOUT

logger = logging.getLogger(__name__)

# A metadata URL is required for saml-integrator to reach active. We use a
# well-known public SAML IdP metadata endpoint so the integrator can fetch
# and parse a real descriptor without requiring a locally-deployed IdP.
_SAML_ENTITY_ID = "https://login.staging.ubuntu.com"
_SAML_METADATA_URL = "https://login.staging.ubuntu.com/saml/metadata"


@pytest.mark.abort_on_fail
def test_saml_integration(app: str, juju: jubilant.Juju, indico_address: str):
    """Check that integrating saml-integrator wires a SAML auth provider.

    arrange: The charm is deployed and active with postgresql and redis.
    act: Deploy saml-integrator pointed at an IdP metadata URL and integrate
        it with indico.
    assert: All applications become active and the Indico login page exposes
        the SAML single sign-on provider.
    """
    juju.deploy(
        "saml-integrator",
        channel="latest/stable",
        trust=True,
        config={
            "entity_id": _SAML_ENTITY_ID,
            "metadata_url": _SAML_METADATA_URL,
        },
    )
    juju.wait(
        lambda status: jubilant.all_active(status, "saml-integrator"),
        timeout=JUJU_WAIT_TIMEOUT,
    )

    juju.integrate(f"{app}:saml", "saml-integrator:saml")
    juju.wait(jubilant.all_active, timeout=JUJU_WAIT_TIMEOUT)
    logger.info("Indico is active after SAML integration")

    # The flask-multipass SAML provider is exposed on /login/ubuntu/; Indico
    # redirects unauthenticated users there to start the SSO flow. The route is
    # registered with a trailing slash, so the canonical URL must be requested
    # directly: /login/ubuntu (no slash) only yields a 308 to /login/ubuntu/.
    response = requests.get(
        f"{indico_address}/login/ubuntu/",
        allow_redirects=False,
        timeout=30,
    )
    assert response.status_code in (
        302,
        303,
    ), f"Expected a redirect to the IdP, got {response.status_code}"
    location = response.headers.get("Location", "")
    idp_host = urlparse(_SAML_ENTITY_ID).netloc
    assert idp_host in location, f"Expected a redirect to the IdP, got {location}"
