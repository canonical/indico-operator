# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for Indico charm integration tests."""

from pathlib import Path
from secrets import token_hex
from typing import Dict, Union

import jubilant
import pytest
import pytest_jubilant
import yaml
from pytest import Config, fixture


def pytest_addoption(parser):
    """Add Indico-specific command-line options.

    Args:
        parser: The pytest argument parser.
    """
    parser.addoption(
        "--charm-file", action="store", default=None, help="Pre-built charm file path"
    )
    parser.addoption("--indico-image", action="store", default=None, help="Indico OCI image")
    parser.addoption(
        "--indico-nginx-image", action="store", default=None, help="Indico nginx OCI image"
    )
    parser.addoption("--saml-email", action="store", default=None, help="SAML test email address")
    parser.addoption("--saml-password", action="store", default=None, help="SAML test password")


@fixture(scope="module", name="external_url")
def external_url_fixture():
    """Provides the external URL for Indico."""
    return "https://events.staging.canonical.com"


@fixture(scope="module")
def saml_email(pytestconfig: Config):
    """SAML login email address test argument for SAML integration tests."""
    email = pytestconfig.getoption("--saml-email")
    if not email:
        raise ValueError("--saml-email argument is required for selected test cases")
    return email


@fixture(scope="module")
def saml_password(pytestconfig: Config):
    """SAML login password test argument for SAML integration tests."""
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
    """Provides a global default timeout for HTTP requests."""
    yield 15


@pytest.fixture(scope="module", name="app")
def app_fixture(
    juju: jubilant.Juju,
    app_name: str,
    pytestconfig: Config,
):
    """Indico charm used for integration testing.

    Builds the charm and deploys it and the relations it depends on.
    """
    postgresql_config: Dict[str, Union[bool, str]] = {
        "plugin_pg_trgm_enable": True,
        "plugin_unaccent_enable": True,
        "profile": "testing",
    }
    juju.deploy("postgresql-k8s", channel="14/edge", config=postgresql_config, trust=True)
    juju.deploy("redis-k8s", "redis-broker", channel="latest/edge")
    juju.deploy("redis-k8s", "redis-cache", channel="latest/edge")
    juju.deploy(
        "nginx-ingress-integrator",
        channel="latest/edge",
        revision=133,
        trust=True,
    )

    resources = {
        "indico-image": pytestconfig.getoption("--indico-image"),
        "indico-nginx-image": pytestconfig.getoption("--indico-nginx-image"),
    }

    if charm := pytestconfig.getoption("--charm-file"):
        juju.deploy(f"./{charm}", app_name, resources=resources)
    else:
        charm = pytest_jubilant.pack()
        juju.deploy(
            charm,
            app_name,
            resources=resources,
            config={
                "external_plugins": "https://github.com/canonical/flask-multipass-saml-groups/releases/download/1.2.2/flask_multipass_saml_groups-1.2.2-py3-none-any.whl"  # noqa: E501 pylint: disable=line-too-long
            },
        )

    juju.integrate(app_name, "postgresql-k8s")
    juju.integrate(f"{app_name}:redis-broker", "redis-broker")
    juju.integrate(f"{app_name}:redis-cache", "redis-cache")
    juju.integrate(app_name, "nginx-ingress-integrator")
    juju.wait(
        lambda status: jubilant.all_active(
            status,
            app_name,
            "postgresql-k8s",
            "redis-broker",
            "redis-cache",
            "nginx-ingress-integrator",
        ),
        error=jubilant.any_error,
    )
    yield app_name


@pytest.fixture(scope="module", name="saml_integrator")
def saml_integrator_fixture(juju: jubilant.Juju, app: str):
    """SAML integrator charm used for integration testing."""
    saml_config = {
        "entity_id": "https://login.staging.ubuntu.com",
        "metadata_url": "https://login.staging.ubuntu.com/saml/metadata",
    }
    juju.deploy("saml-integrator", channel="latest/stable", config=saml_config, trust=True)
    juju.integrate(app, "saml-integrator")
    juju.wait(
        lambda status: jubilant.all_active(status, "saml-integrator", app),
        error=jubilant.any_error,
    )
    yield "saml-integrator"


@pytest.fixture(scope="module", name="s3_integrator")
def s3_integrator_fixture(juju: jubilant.Juju, app: str):
    """S3 integrator charm used for integration testing."""
    s3_config = {
        "bucket": "some-bucket",
        "endpoint": "s3.example.com",
    }
    juju.deploy("s3-integrator", channel="latest/edge", config=s3_config)
    juju.wait(lambda status: jubilant.all_blocked(status, "s3-integrator"))
    params = {"access-key": token_hex(16), "secret-key": token_hex(16)}
    juju.run("s3-integrator/0", "sync-s3-credentials", params=params)
    juju.wait(
        lambda status: jubilant.all_active(status, "s3-integrator"),
        error=jubilant.any_error,
    )
    juju.integrate(app, "s3-integrator")
    juju.wait(
        lambda status: jubilant.all_active(status, "s3-integrator", app),
        error=jubilant.any_error,
    )
    yield "s3-integrator"


@pytest.fixture(scope="module", name="loki")
def loki_fixture(juju: jubilant.Juju, app: str):
    """Loki charm used for integration testing."""
    juju.deploy("loki-k8s", channel="1/edge", trust=True, revision=97)
    juju.integrate(app, "loki-k8s")
    juju.wait(
        lambda status: jubilant.all_active(status, "loki-k8s", app),
        error=jubilant.any_error,
    )
    yield "loki-k8s"
