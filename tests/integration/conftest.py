# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for Indico charm integration tests."""

import asyncio
import glob
from pathlib import Path
from typing import Dict

import pytest_asyncio
import yaml
from ops.model import WaitingStatus
from pytest import Config, fixture
from pytest_operator.plugin import OpsTest


@fixture(scope="module")
def saml_email(pytestconfig: Config):
    """SAML login email address test argument for SAML integration tests"""
    email = pytestconfig.getoption("--saml-email")
    if not email:
        raise ValueError("--saml-email argument is required for selected test cases")
    return email


@fixture(scope="module")
def saml_password(pytestconfig: Config):
    """SAML login password test argument for SAML integration tests"""
    password = pytestconfig.getoption("--saml-password")
    if not password:
        raise ValueError("--saml-password argument is required for selected test cases")
    return password


@fixture(scope="module", name="metadata")
def metadata_fixture():
    """Provides charm metadata."""
    yield yaml.safe_load(Path("./metadata.yaml").read_text("utf-8"))


@fixture(scope="module", name="app_name")
def app_name_fixture(metadata):
    """Provides app name from the metadata."""
    yield metadata["name"]


@fixture(scope="module", name="prometheus_exporter_images")
def prometheus_exporter_images_fixture(metadata):
    """Provides Prometheus exporter images from the metadata."""
    prometheus_exporter_images = {
        "nginx-prometheus-exporter-image": metadata["resources"][
            "nginx-prometheus-exporter-image"
        ]["upstream-source"],
        "statsd-prometheus-exporter-image": metadata["resources"][
            "statsd-prometheus-exporter-image"
        ]["upstream-source"],
        "celery-prometheus-exporter-image": metadata["resources"][
            "celery-prometheus-exporter-image"
        ]["upstream-source"],
    }
    yield prometheus_exporter_images


@fixture(scope="module")
def requests_timeout():
    """Provides a global default timeout for HTTP requests"""
    yield 15


@pytest_asyncio.fixture(scope="module")
async def app(
    ops_test: OpsTest,
    app_name: str,
    pytestconfig: Config,
    prometheus_exporter_images: Dict[str, str],
):
    """Indico charm used for integration testing.

    Builds the charm and deploys it and the relations it depends on.
    """
    assert ops_test.model
    # Deploy relations to speed up overall execution
    dependencies = asyncio.gather(
        ops_test.model.deploy("postgresql-k8s"),
        ops_test.model.deploy("redis-k8s", "redis-broker"),
        ops_test.model.deploy("redis-k8s", "redis-cache"),
        ops_test.model.deploy("nginx-ingress-integrator", trust=True),
    )

    resources = {
        "indico-image": pytestconfig.getoption("--indico-image"),
        "indico-nginx-image": pytestconfig.getoption("--indico-nginx-image"),
    }
    resources.update(prometheus_exporter_images)
    cached = glob.glob("**/*.charm", recursive=True)
    if len(cached) >= 1:
        charm = Path(cached[0])
    else:
        charm = await ops_test.build_charm(".")
    application = await ops_test.model.deploy(
        charm, resources=resources, application_name=app_name, series="focal"
    )

    await dependencies
    # Add required relations, mypy has difficulty with WaitingStatus
    expected_name = WaitingStatus.name  # type: ignore
    assert ops_test.model.applications[app_name].units[0].workload_status == expected_name
    await asyncio.gather(
        ops_test.model.add_relation(app_name, "postgresql-k8s:db"),
        ops_test.model.add_relation(app_name, "redis-broker"),
        ops_test.model.add_relation(app_name, "redis-cache"),
        ops_test.model.add_relation(app_name, "nginx-ingress-integrator"),
    )
    await ops_test.model.wait_for_idle(status="active", raise_on_error=False)

    yield application
