# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for Indico charm integration tests."""

import asyncio
from pathlib import Path

import pytest_asyncio
import yaml
from pytest import Config, fixture
from pytest_operator.plugin import OpsTest

from tests.integration.helpers import app_add_relation, deploy_app, deploy_related_charm


@fixture(scope="module", name="metadata")
def metadata_fixture():
    """Provides charm metadata."""
    yield yaml.safe_load(Path("./metadata.yaml").read_text("utf-8"))


@fixture(scope="module", name="app_name")
def app_name_fixture(metadata):
    """Provides app name from the metadata."""
    yield metadata["name"]


@fixture(scope="module", name="nginx_prometheus_exporter_image")
def nginx_prometheus_exporter_image_fixture(metadata):
    """Provides the nginx prometheus exporter image from the metadata."""
    yield metadata["resources"]["nginx-prometheus-exporter-image"]["upstream-source"]


@fixture(scope="module", name="statsd_prometheus_exporter_image")
def statsd_prometheus_exporter_image_fixture(metadata):
    """Provides the statsd prometheus exporter image from the metadata."""
    yield metadata["resources"]["statsd-prometheus-exporter-image"]["upstream-source"]


@fixture(scope="module", name="celery_prometheus_exporter_image")
def celery_prometheus_exporter_image_fixture(metadata):
    """Provides the celery prometheus exporter image from the metadata."""
    yield metadata["resources"]["celery-prometheus-exporter-image"]["upstream-source"]


@pytest_asyncio.fixture(scope="module")
async def app(
    ops_test: OpsTest,
    app_name: str,
    pytestconfig: Config,
    nginx_prometheus_exporter_image: str,
    statsd_prometheus_exporter_image: str,
    celery_prometheus_exporter_image: str,
):  # pylint:disable=R0913
    """Indico charm used for integration testing.

    Builds the charm and deploys it and the relations it depends on.
    """
    assert ops_test.model
    # Deploy relations to speed up overall execution
    await asyncio.gather(
        deploy_related_charm(ops_test, "postgresql-k8s", raise_on_error=False),
        deploy_related_charm(ops_test, "redis-k8s", "redis-broker"),
        deploy_related_charm(ops_test, "redis-k8s", "redis-cache"),
        deploy_related_charm(ops_test, "nginx-ingress-integrator", trust=True),
    )
    await ops_test.model.wait_for_idle()

    application = await deploy_app(
        ops_test,
        app_name,
        series="focal",
        resources={
            "indico-image": pytestconfig.getoption("--indico-image"),
            "indico-nginx-image": pytestconfig.getoption("--indico-nginx-image"),
            "nginx-prometheus-exporter-image": nginx_prometheus_exporter_image,
            "statsd-prometheus-exporter-image": statsd_prometheus_exporter_image,
            "celery-prometheus-exporter-image": celery_prometheus_exporter_image,
        },
    )
    await ops_test.model.wait_for_idle()

    await asyncio.gather(
        app_add_relation(ops_test, app_name, "postgresql-k8s:db"),
        app_add_relation(ops_test, app_name, "redis-broker:redis"),
        app_add_relation(ops_test, app_name, "redis-cache:redis"),
        app_add_relation(ops_test, app_name, "nginx-ingress-integrator"),
    )
    await ops_test.model.wait_for_idle(status="active")

    yield application
