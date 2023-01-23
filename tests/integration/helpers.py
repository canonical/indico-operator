#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Helper functions for integration tests.

These helper functions will deploy charms or add relations only if they do not already exists.
"""

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


async def deploy_app(
    ops_test: OpsTest,
    app_name: str,
    series: str,
    resources: Optional[dict] = None,
) -> Application:
    """Deploy our main app, if it's not already deployed."""
    assert ops_test.model
    if resources is None:
        resources = {}
    if app_name not in ops_test.model.applications:
        charm = await ops_test.build_charm(".")
        application = await ops_test.model.deploy(
            charm, resources=resources, application_name=app_name, series=series
        )
        await ops_test.model.wait_for_idle()
        return application
    return ops_test.model.applications[app_name]


async def relate_app(
    ops_test: OpsTest,
    app_name: str,
    relation_id: str,
):
    """Relate to applications if the relation does not already exists."""
    assert ops_test.model
    assert ops_test.model.relations

    if not any(relation for relation in ops_test.model.relations if relation.matches(relation_id)):
        await ops_test.model.add_relation(app_name, relation_id)
