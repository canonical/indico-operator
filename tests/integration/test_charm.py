#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Indico charm integration tests."""

import re
import socket
from unittest.mock import patch
from urllib.parse import urlparse

import pytest
import requests
import urllib3.exceptions
from ops.model import Application
from pytest_operator.plugin import OpsTest

from charm import CELERY_PROMEXP_PORT, NGINX_PROMEXP_PORT, STATSD_PROMEXP_PORT


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
@pytest.mark.usefixtures("app")
async def test_indico_is_up(ops_test: OpsTest, external_url: str):
    """Check that the bootstrap page is reachable.

    Assume that the charm has already been built and is running.
    """
    assert ops_test.model
    # Send request to bootstrap page and set Host header to app_name (which the application
    # expects)
    host = urlparse(external_url).netloc
    # The certificate is not signed
    response = requests.get(  # nosec
        "https://127.0.0.1/bootstrap", headers={"Host": host}, timeout=10, verify=False
    )
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_health_checks(app: Application):
    """Runs health checks for each container.

    Assume that the charm has already been built and is running.
    """
    container__checks_list = [("indico-nginx", 2), ("indico", 4)]
    # Application actually does have units
    indico_unit = app.units[0]  # type: ignore
    for container_checks in container__checks_list:
        container = container_checks[0]
        cmd = f"PEBBLE_SOCKET=/charm/containers/{container}/pebble.socket /charm/bin/pebble checks"
        action = await indico_unit.run(cmd, timeout=10)
        # Change this if upgrading Juju lib version to >= 3
        # See https://github.com/juju/python-libjuju/issues/707#issuecomment-1212296289
        result = action.data
        code = result["results"].get("Code")
        stdout = result["results"].get("Stdout")
        stderr = result["results"].get("Stderr")
        assert code == "0", f"{cmd} failed ({code}): {stderr or stdout}"
        # When executing the checks, `0/3` means there are 0 errors of 3.
        # Each check has it's own `0/3`, so we will count `n` times,
        # where `n` is the number of checks for that container.
        assert stdout.count("0/3") == container_checks[1]


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_prom_exporters_are_up(app: Application):
    """
    arrange: given charm in its initial state
    act: when the metrics endpoints are scraped
    assert: the response is 200 (HTTP OK)
    """
    # Application actually does have units
    indico_unit = app.units[0]  # type: ignore
    prometheus_targets = [
        f"localhost:{NGINX_PROMEXP_PORT}",
        f"localhost:{STATSD_PROMEXP_PORT}",
        f"localhost:{CELERY_PROMEXP_PORT}",
    ]
    # Send request to /metrics for each target and check the response
    for target in prometheus_targets:
        cmd = f"curl -m 10 http://{target}/metrics"
        action = await indico_unit.run(cmd, timeout=15)
        # Change this if upgrading Juju lib version to >= 3
        # See https://github.com/juju/python-libjuju/issues/707#issuecomment-1212296289
        result = action.data
        code = result["results"].get("Code")
        stdout = result["results"].get("Stdout")
        stderr = result["results"].get("Stderr")
        assert code == "0", f"{cmd} failed ({code}): {stderr or stdout}"


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
@pytest.mark.usefixtures("saml_integrator")
async def test_saml_auth(
    saml_email: str, saml_password: str, requests_timeout: float, external_url: str
):
    """
    arrange: given charm in its initial state
    act: configure and integrate the SAML integrator fire SAML authentication
    assert: The SAML authentication process is executed successfully.
    """
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
        login_page = session.get(
            f"https://{host}/login",
            verify=False,
            timeout=requests_timeout,
        )
        csrf_token_matches = re.findall(
            "<input type='hidden' name='csrfmiddlewaretoken' value='([^']+)' />", login_page.text
        )
        assert csrf_token_matches, login_page.text
        saml_callback = session.post(
            "https://login.staging.ubuntu.com/+login",
            data={
                "csrfmiddlewaretoken": csrf_token_matches[0],
                "email": saml_email,
                "user-intentions": "login",
                "password": saml_password,
                "next": "/saml/process",
                "continue": "",
                "openid.usernamesecret": "",
                "RelayState": "events.staging.canonical.com",
            },
            headers={"Referer": login_page.url},
            timeout=requests_timeout,
        )
        saml_response_matches = re.findall(
            '<input type="hidden" name="SAMLResponse" value="([^"]+)" />', saml_callback.text
        )
        assert len(saml_response_matches), saml_callback.text
        session.post(
            f"https://{host}/multipass/saml/ubuntu/acs",
            data={
                "RelayState": "None",
                "SAMLResponse": saml_response_matches[0],
                "openid.usernamesecret": "",
            },
            verify=False,
            timeout=requests_timeout,
        )
        session.post(
            f"https://{host}/multipass/saml/ubuntu/acs",
            data={"SAMLResponse": saml_response_matches[0], "SameSite": "1"},
            verify=False,
            timeout=requests_timeout,
        )

        dashboard_page = session.get(
            f"https://{host}/register/ubuntu",
            verify=False,
            timeout=requests_timeout,
        )
        assert dashboard_page.status_code == 200
