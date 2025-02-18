#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Indico charm actions integration tests."""

from secrets import token_hex

import juju.action
import pytest
import pytest_asyncio
from ops import Application

ADMIN_USER_EMAIL = "sample@email.com"
ADMIN_USER_EMAIL_FAIL = "sample2@email.com"


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
    password = token_hex(16)

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
