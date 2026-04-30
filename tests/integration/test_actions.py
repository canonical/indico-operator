#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Indico charm actions integration tests."""

from secrets import token_hex

import jubilant
import pytest

ADMIN_USER_EMAIL = "sample@email.com"
ADMIN_USER_EMAIL_FAIL = "sample2@email.com"


@pytest.fixture(scope="module")
def add_admin(juju: jubilant.Juju, app: str):
    """
    arrange: given charm in its initial state
    act: run the add-admin action
    assert: check the output in the action result
    """
    email = ADMIN_USER_EMAIL
    email_fail = ADMIN_USER_EMAIL_FAIL
    # This is a test password
    password = token_hex(16)

    task = juju.run(f"{app}/0", "add-admin", params={"email": email, "password": password})
    assert task.success
    assert task.results["user"] == email
    assert f'Admin with email "{email}" correctly created' in task.results["output"]

    task2 = juju.run(f"{app}/0", "add-admin", params={"email": email_fail, "password": password})
    assert task2.success
    assert task2.results["user"] == email_fail
    assert f'Admin with email "{email_fail}" correctly created' in task2.results["output"]


@pytest.mark.abort_on_fail
@pytest.mark.usefixtures("add_admin")
def test_anonymize_user(juju: jubilant.Juju, app: str):
    """
    arrange: admin user created
    act: run the anonymize-user action
    assert: check the output in the action result
    """
    task = juju.run(f"{app}/0", "anonymize-user", params={"email": ADMIN_USER_EMAIL})
    assert task.success
    assert task.results["user"] == ADMIN_USER_EMAIL
    expected_words = [ADMIN_USER_EMAIL, "correctly anonymized"]
    assert all(word in task.results["output"] for word in expected_words)


@pytest.mark.abort_on_fail
@pytest.mark.usefixtures("add_admin")
def test_anonymize_user_fail(juju: jubilant.Juju, app: str):
    """
    arrange: admin user created
    act: run the anonymize-user action
    assert: check the output in the action result
    """
    with pytest.raises(jubilant.TaskError) as exc_info:
        juju.run(f"{app}/0", "anonymize-user", params={"email": f",{ADMIN_USER_EMAIL_FAIL}"})
    task = exc_info.value.task
    assert task.status == "failed"
    assert task.results["user"] == f",{ADMIN_USER_EMAIL_FAIL}"
    expected_words = [ADMIN_USER_EMAIL_FAIL, "correctly anonymized", "Failed to anonymize user"]
    assert all(word in task.results["output"] for word in expected_words)
