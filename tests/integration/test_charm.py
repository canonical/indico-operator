#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Indico charm integration tests."""

import logging
import re
import socket
from unittest.mock import patch

import juju.action
import pytest
import pytest_asyncio
import requests
import urllib3.exceptions
from ops.model import ActiveStatus, Application
from pytest_operator.plugin import OpsTest

from charm import (
    CELERY_PROMEXP_PORT,
    NGINX_PROMEXP_PORT,
    STAGING_UBUNTU_SAML_URL,
    STATSD_PROMEXP_PORT,
)

ADMIN_USER_EMAIL = "sample@email.com"
ADMIN_USER_EMAIL_FAIL = "sample2@email.com"

logger = logging.getLogger()


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_active(app: Application):
    """Check that the charm is active.

    Assume that the charm has already been built and is running.
    """
    # Application actually does have units
    assert app.units[0].workload_status == ActiveStatus.name  # type: ignore


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_indico_is_up(ops_test: OpsTest, app: Application):
    """Check that the bootstrap page is reachable.

    Assume that the charm has already been built and is running.
    """
    assert ops_test.model
    # Read the IP address of indico
    status = await ops_test.model.get_status()
    unit = list(status.applications[app.name].units)[0]
    address = status["applications"][app.name]["units"][unit]["address"]
    # Send request to bootstrap page and set Host header to app_name (which the application
    # expects)
    response = requests.get(
        f"http://{address}:8080/bootstrap", headers={"Host": f"{app.name}.local"}, timeout=10
    )
    assert response.status_code == 200


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
        result = action.data
        code = result["results"].get("Code")
        stdout = result["results"].get("Stdout")
        stderr = result["results"].get("Stderr")
        assert code == "0", f"{cmd} failed ({code}): {stderr or stdout}"


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
async def test_health_checks(app: Application):
    """Runs health checks for each container.

    Assume that the charm has already been built and is running.
    """
    container_list = ["indico", "indico-nginx", "indico-celery"]
    # Application actually does have units
    indico_unit = app.units[0]  # type: ignore
    for container in container_list:
        cmd = f"PEBBLE_SOCKET=/charm/containers/{container}/pebble.socket /charm/bin/pebble checks"
        action = await indico_unit.run(cmd, timeout=10)
        result = action.data
        code = result["results"].get("Code")
        stdout = result["results"].get("Stdout")
        stderr = result["results"].get("Stderr")
        assert code == "0", f"{cmd} failed ({code}): {stderr or stdout}"
        # When executing the checks, `0/3` means there are 0 errors of 3.
        # Each check has it's own `0/3`, so we will count `n` times,
        # where `n` is the number of checks for that container.
        assert stdout.count("0/3") == 1


@pytest.mark.abort_on_fail
@pytest_asyncio.fixture(scope="module")
async def add_admin(app: Application):
    """
    arrange: given charm in its initial state
    act: run the add-admin action
    assert: check the output in the action result
    """
    assert hasattr(app, "units")

    assert app.units[0]

    email = ADMIN_USER_EMAIL
    email_fail = ADMIN_USER_EMAIL_FAIL
    # This is a test password
    password = "somepassword"  # nosec

    # Application actually does have units
    action: juju.action.Action = await app.units[0].run_action(  # type: ignore
        "add-admin", email=email, password=password
    )
    await action.wait()
    assert action.status == "completed"
    assert action.results["user"] == email
    assert f'Admin with email "{email}" correctly created' in action.results["output"]
    action2: juju.action.Action = await app.units[0].run_action(  # type: ignore
        "add-admin", email=email_fail, password=password
    )
    await action2.wait()
    assert action2.status == "completed"
    assert action2.results["user"] == email_fail
    assert f'Admin with email "{email_fail}" correctly created' in action2.results["output"]


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
@pytest.mark.usefixtures("add_admin")
async def test_anonymize_user(app: Application):
    """
    arrange: admin user created
    act: run the anonymize-user action
    assert: check the output in the action result
    """
    # Application actually does have units
    action_anonymize: juju.action.Action = await app.units[0].run_action(  # type: ignore
        "anonymize-user", email=ADMIN_USER_EMAIL
    )
    await action_anonymize.wait()
    assert action_anonymize.status == "completed"
    assert action_anonymize.results["user"] == ADMIN_USER_EMAIL
    expected_words = [ADMIN_USER_EMAIL, "correctly anonymized"]
    assert all(word in action_anonymize.results["output"] for word in expected_words)


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
@pytest.mark.usefixtures("add_admin")
async def test_anonymize_user_fail(app: Application):
    """
    arrange: admin user created
    act: run the anonymize-user action
    assert: check the output in the action result
    """
    # Application actually does have units
    action_anonymize: juju.action.Action = await app.units[0].run_action(  # type: ignore
        "anonymize-user", email=f",{ADMIN_USER_EMAIL_FAIL}"
    )
    await action_anonymize.wait()
    assert action_anonymize.status == "failed"
    assert action_anonymize.results["user"] == f",{ADMIN_USER_EMAIL_FAIL}"
    expected_words = [ADMIN_USER_EMAIL_FAIL, "correctly anonymized", "Failed to anonymize user"]
    assert all(word in action_anonymize.results["output"] for word in expected_words)


@pytest.mark.asyncio
@pytest.mark.abort_on_fail
@pytest.mark.requires_secrets
async def test_saml_auth(
    ops_test: OpsTest,
    app: Application,
    saml_email: str,
    saml_password: str,
    requests_timeout: float,
):
    """
    arrange: given charm in its initial state
    act: configure a SAML target url and fire SAML authentication
    assert: The SAML authentication process is executed successfully.
    """
    # The linter does not recognize set_config as a method, so this errors must be ignored.
    await app.set_config(  # type: ignore[attr-defined] # pylint: disable=W0106
        {
            "site_url": "https://indico.local",
            "saml_target_url": STAGING_UBUNTU_SAML_URL,
        }
    )
    # The linter does not recognize wait_for_idle as a method,
    # since ops_test has a model as Optional, so this error must be ignored.
    await ops_test.model.wait_for_idle(status="active")  # type: ignore[union-attr]
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    host = "indico.local"
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
        dashboard_page = session.get(
            f"https://{host}/user/dashboard/",
            verify=False,
            allow_redirects=False,
            timeout=requests_timeout,
        )
        assert dashboard_page.status_code == 302

        session.get(f"https://{host}", verify=False)
        login_page = session.get(
            f"https://{host}/login",
            verify=False,
            timeout=requests_timeout,
        )
        csrf_token_matches = re.findall(
            "<input type='hidden' name='csrfmiddlewaretoken' value='([^']+)' />", login_page.text
        )
        assert len(csrf_token_matches) > 0
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
                "RelayState": "indico.local",
            },
            headers={"Referer": login_page.url},
            timeout=requests_timeout,
        )
        saml_response_matches = re.findall(
            '<input type="hidden" name="SAMLResponse" value="([^"]+)" />', saml_callback.text
        )
        assert len(saml_response_matches) > 0
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
            allow_redirects=False,
            timeout=requests_timeout,
        )
        assert dashboard_page.status_code == 200
