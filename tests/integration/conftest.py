# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for Indico charm integration tests."""

import asyncio
from pathlib import Path
from secrets import token_hex

import pytest_asyncio
import yaml
from ops import Application
from pytest import Config, fixture
from pytest_operator.plugin import OpsTest


@fixture(scope="module", name="external_url")
def external_url_fixture():
    """Provides the external URL for Indico."""
    return "https://events.staging.canonical.com"


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


@fixture(scope="module")
def requests_timeout():
    """Provides a global default timeout for HTTP requests"""
    yield 15


@pytest_asyncio.fixture(scope="module", name="app")
async def app_fixture(
    ops_test: OpsTest,
    app_name: str,
    pytestconfig: Config,
):
    """Indico charm used for integration testing.

    Builds the charm and deploys it and the relations it depends on.
    """
    assert ops_test.model
    # Deploy relations to speed up overall execution
    postgresql_config = {
        "plugin_pg_trgm_enable": str(True),
        "plugin_unaccent_enable": str(True),
        "profile": "testing",
    }
    await asyncio.gather(
        ops_test.model.deploy(
            "postgresql-k8s", channel="14/edge", config=postgresql_config, trust=True
        ),
        ops_test.model.deploy("redis-k8s", "redis-broker", channel="latest/edge"),
        ops_test.model.deploy("redis-k8s", "redis-cache", channel="latest/edge"),
        ops_test.model.deploy(
            "nginx-ingress-integrator", channel="latest/edge", series="focal", trust=True
        ),
    )
    await ops_test.model.wait_for_idle(
        apps=["postgresql-k8s"], status="active", raise_on_error=False
    )
    resources = {
        "indico-image": pytestconfig.getoption("--indico-image"),
        "indico-nginx-image": pytestconfig.getoption("--indico-nginx-image"),
    }

    if charm := pytestconfig.getoption("--charm-file"):
        application = await ops_test.model.deploy(
            f"./{charm}",
            resources=resources,
            application_name=app_name,
            series="focal",
        )
    else:
        charm = await ops_test.build_charm(".")
        application = await ops_test.model.deploy(
            charm,
            resources=resources,
            application_name=app_name,
            series="focal",
        )

    await asyncio.gather(
        ops_test.model.add_relation(app_name, "postgresql-k8s"),
        ops_test.model.add_relation(f"{app_name}:redis-broker", "redis-broker"),
        ops_test.model.add_relation(f"{app_name}:redis-cache", "redis-cache"),
        ops_test.model.add_relation(app_name, "nginx-ingress-integrator"),
    )
    await ops_test.model.wait_for_idle(status="active", raise_on_error=False)

    # Install saml_groups plugin
    await application.set_config(
        {
            "external_plugins": "https://github.com/canonical/flask-multipass-saml-groups/releases/download/1.2.1/flask_multipass_saml_groups-1.2.1-py3-none-any.whl"
        }
    )
    yield application


@pytest_asyncio.fixture(scope="module", name="saml_integrator")
async def saml_integrator_fixture(ops_test: OpsTest, app: Application):
    """SAML integrator charm used for integration testing."""
    assert ops_test.model
    saml_config = {
        "entity_id": "https://login.staging.ubuntu.com",
        "metadata_url": "https://login.staging.ubuntu.com/saml/metadata",
    }
    saml_integrator = await ops_test.model.deploy(
        "saml-integrator", channel="latest/stable", config=saml_config, trust=True
    )
    await ops_test.model.add_relation(app.name, saml_integrator.name)
    await ops_test.model.wait_for_idle(
        apps=[saml_integrator.name, app.name], status="active", raise_on_error=False
    )
    yield saml_integrator


@pytest_asyncio.fixture(scope="module", name="s3_integrator")
async def s3_integrator_fixture(ops_test: OpsTest, app: Application):
    """SAML integrator charm used for integration testing."""
    assert ops_test.model
    s3_config = {
        "bucket": "some-bucket",
        "endpoint": "s3.example.com",
    }
    s3_integrator = await ops_test.model.deploy(
        "s3-integrator", channel="latest/edge", config=s3_config
    )
    await ops_test.model.wait_for_idle(apps=[s3_integrator.name], idle_period=5, status="blocked")
    params = {"access-key": token_hex(16), "secret-key": token_hex(16)}
    # Application actually does have units
    action_sync_s3_credentials = await s3_integrator.units[0].run_action(  # type: ignore
        "sync-s3-credentials", **params
    )
    await action_sync_s3_credentials.wait()
    await ops_test.model.wait_for_idle(
        apps=[s3_integrator.name], status="active", raise_on_error=False
    )
    await ops_test.model.add_relation(app.name, s3_integrator.name)
    await ops_test.model.wait_for_idle(
        apps=[s3_integrator.name, app.name], status="active", raise_on_error=False
    )
    yield s3_integrator
