#!/usr/bin/env python3
# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

from typing import Optional

from ops.model import Application, Relation
from pytest_operator.plugin import OpsTest


async def deploy_related_charm(
    ops_test: OpsTest,
    charm_name: str,
    instance_name: Optional[str] = None,
    raise_on_error: bool = True,
    trust: bool = False,
) -> Application:
    assert ops_test.model
    instance_name = instance_name or charm_name
    if instance_name not in ops_test.model.applications:
        instance = await ops_test.model.deploy(charm_name, instance_name)
        await ops_test.model.wait_for_idle(raise_on_error=raise_on_error, trust=trust)
        return instance
    return ops_test.model.applications[instance_name]


async def deploy_app(
    ops_test: OpsTest,
    app_name: str,
    series: str,
    resources: dict = {},
) -> Application:
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
    assert ops_test.model
    assert ops_test.model.relations

    # this function is defined here to be typed
    def rmatch(rel: Relation, relation_id: str) -> bool:
        return rel.matches(relation_id)

    if not any(filter(lambda x: rmatch(x, relation_id), ops_test.model.relations)):
        await ops_test.model.add_relation(app_name, relation_id),
