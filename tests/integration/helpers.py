#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Helper functions for integration tests."""

from typing import Optional

from ops.model import Application
from pytest_operator.plugin import OpsTest


async def deploy_related_charm(
    ops_test: OpsTest,
    charm_name: str,
    instance_name: Optional[str] = None,
    raise_on_error: bool = True,
    trust: bool = False,
) -> Application:
    """Deploy a charm related to our main app, if it's not already deployed."""
    assert ops_test.model
    instance_name = instance_name or charm_name
    if instance_name not in ops_test.model.applications:
        instance = await ops_test.model.deploy(charm_name, instance_name, trust=trust)
        await ops_test.model.wait_for_idle(raise_on_error=raise_on_error)
        return instance
    return ops_test.model.applications[instance_name]


# pylint: disable=dangerous-default-value
async def deploy_app(
    ops_test: OpsTest,
    app_name: str,
    series: str,
    resources: dict = {},
) -> Application:
    """Deploy our main app, if it's not already deployed."""
    assert ops_test.model
    if app_name not in ops_test.model.applications:
        charm = await ops_test.build_charm(".")
        application = await ops_test.model.deploy(
            charm, resources=resources, application_name=app_name, series=series
        )
        await ops_test.model.wait_for_idle()
        return application
    return ops_test.model.applications[app_name]


async def app_add_relation(
    ops_test: OpsTest,
    app_name: str,
    relation_id: str,
):
    """Relate to applications if the relation does not already exists."""
    assert ops_test.model
    assert ops_test.model.relations

    if not any(filter(lambda x: x.matches(relation_id), ops_test.model.relations)):  # type: ignore
        await ops_test.model.add_relation(app_name, relation_id)


async def get_unit_address(ops_test: OpsTest, app_name: str) -> str:
    """Get unit IP address.
    Args:
        ops_test: The ops test framework instance
        app_name: The name of the app
    Returns:
        IP address of the first unit
    """
    assert ops_test.model
    status = await ops_test.model.get_status()
    unit = list(status.applications[app_name].units)[0]
    return status["applications"][app_name]["units"][unit]["address"]
