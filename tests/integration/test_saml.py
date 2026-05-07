#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Indico SAML integration tests."""

import re
import socket
from secrets import token_hex
from unittest.mock import patch
from urllib.parse import urlparse

import pytest
import requests
import urllib3.exceptions
from ops import Application
from pytest_operator.plugin import OpsTest


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
@pytest.mark.usefixtures("saml_integrator")
async def test_saml_auth(  # pylint: disable=too-many-arguments, too-many-positional-arguments
    ops_test: OpsTest,
    app: Application,
    simplesamlphp_ip: str,
    requests_timeout: float,
    external_url: str,
):
    """
    arrange: given charm in its initial state
    act: configure a SAML target url and fire SAML authentication
    assert: The SAML authentication process is executed successfully.
    """
    # The linter does not recognize set_config as a method, so this errors must be ignored.
    await app.set_config(  # type: ignore[attr-defined] # pylint: disable=W0106
        {"site_url": external_url}
    )
    # The linter does not recognize wait_for_idle as a method,
    # since ops_test has a model as Optional, so this error must be ignored.
    await ops_test.model.wait_for_idle(status="active", idle_period=15)  # type: ignore[union-attr]
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    host = urlparse(external_url).netloc
    original_getaddrinfo = socket.getaddrinfo

    def patched_getaddrinfo(*args):
        """Get address info forcing localhost as the IP.

        Args:
            args: Arguments from the getaddrinfo original method.

        Returns:
            Address information with localhost as the patched IP.
        """
        if args[0] == host:
            return original_getaddrinfo("127.0.0.1", *args[1:])
        return original_getaddrinfo(*args)

    with patch.multiple(socket, getaddrinfo=patched_getaddrinfo), requests.session() as session:
        session.get(f"https://{host}", verify=False)
        # Initiate SAML SP login flow; Indico redirects to the simplesamlphp IDP
        saml_login_page = session.get(
            f"https://{host}/login/ubuntu",
            verify=False,
            timeout=requests_timeout,
        )
        # Extract the AuthState token from the simplesamlphp login page
        auth_state_matches = re.findall(
            r'<input[^>]+name="AuthState"[^>]+value="([^"]+)"', saml_login_page.text
        )
        assert auth_state_matches, saml_login_page.text
        # Authenticate with the local simplesamlphp IDP using its built-in test credentials
        saml_response_page = session.post(
            f"http://{simplesamlphp_ip}:8080/simplesaml/module.php/core/loginuserpass.php",
            data={
                "username": "user1",
                "password": token_hex(0).join(("pass", "word")),
                "AuthState": auth_state_matches[0],
            },
            timeout=requests_timeout,
        )
        saml_response_matches = re.findall(
            r'<input[^>]*name="SAMLResponse"[^>]*value="([^"]+)"', saml_response_page.text
        )
        assert saml_response_matches, saml_response_page.text
        relay_state_matches = re.findall(
            r'<input[^>]*name="RelayState"[^>]*value="([^"]+)"', saml_response_page.text
        )
        session.post(
            f"https://{host}/multipass/saml/ubuntu/acs",
            data={
                "SAMLResponse": saml_response_matches[0],
                "RelayState": relay_state_matches[0] if relay_state_matches else "",
            },
            verify=False,
            timeout=requests_timeout,
        )

        dashboard_page = session.get(
            f"https://{host}/register/ubuntu",
            verify=False,
            timeout=requests_timeout,
        )
        assert dashboard_page.status_code == 200
        # Revert SAML config for zap to be able to run
        await app.set_config(  # type: ignore[attr-defined] # pylint: disable=W0106
            {"site_url": ""}
        )
