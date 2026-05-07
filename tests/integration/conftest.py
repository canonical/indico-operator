# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for Indico charm integration tests."""

import asyncio
import logging
import time
from pathlib import Path
from secrets import token_hex

import kubernetes
import pytest_asyncio
import yaml
from ops import Application
from pytest import Config, fixture
from pytest_operator.plugin import OpsTest

logger = logging.getLogger(__name__)

SIMPLESAMLPHP_PORT = 8080
SIMPLESAMLPHP_POD_NAME = "simplesamlphp"
SIMPLESAMLPHP_SERVICE_NAME = "simplesamlphp-service"


@fixture(scope="module", name="external_url")
def external_url_fixture():
    """Provides the external URL for Indico."""
    return "https://events.staging.canonical.com"


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
            "nginx-ingress-integrator",
            channel="latest/edge",
            revision=133,
            trust=True,
            series="focal",
        ),
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
            config={
                "external_plugins": "https://github.com/canonical/flask-multipass-saml-groups/releases/download/1.2.2/flask_multipass_saml_groups-1.2.2-py3-none-any.whl"  # noqa: E501 pylint: disable=line-too-long
            },
            series="focal",
        )

    await asyncio.gather(
        ops_test.model.add_relation(app_name, "postgresql-k8s"),
        ops_test.model.add_relation(f"{app_name}:redis-broker", "redis-broker"),
        ops_test.model.add_relation(f"{app_name}:redis-cache", "redis-cache"),
        ops_test.model.add_relation(app_name, "nginx-ingress-integrator"),
    )
    await ops_test.model.wait_for_idle(
        apps=[
            application.name,
            "postgresql-k8s",
            "redis-broker",
            "redis-cache",
            "nginx-ingress-integrator",
        ],
        status="active",
        raise_on_error=True,
    )
    yield application


@pytest_asyncio.fixture(scope="module", name="simplesamlphp_ip")
async def simplesamlphp_ip_fixture(
    pytestconfig: Config,
    ops_test: OpsTest,
    app: Application,  # pylint: disable=unused-argument
    external_url: str,
) -> str:
    """Deploy test SimpleSAML IDP service.

    Returns the pod IP of the deployed application.
    """
    kube_config = pytestconfig.getoption("--kube-config")
    kubernetes.config.load_kube_config(config_file=kube_config)
    assert ops_test.model
    namespace = ops_test.model.name
    v1 = kubernetes.client.CoreV1Api()
    pod = kubernetes.client.V1Pod(
        api_version="v1",
        kind="Pod",
        metadata=kubernetes.client.V1ObjectMeta(
            name=SIMPLESAMLPHP_POD_NAME,
            namespace=namespace,
            labels={"app.kubernetes.io/name": SIMPLESAMLPHP_POD_NAME},
        ),
        spec=kubernetes.client.V1PodSpec(
            containers=[
                kubernetes.client.V1Container(
                    name="saml",
                    image="kenchan0130/simplesamlphp",
                    ports=[
                        kubernetes.client.V1ContainerPort(container_port=SIMPLESAMLPHP_PORT),
                    ],
                    env=[
                        kubernetes.client.V1EnvVar(
                            name="SIMPLESAMLPHP_SP_ENTITY_ID",
                            value=external_url,
                        ),
                        kubernetes.client.V1EnvVar(
                            name="SIMPLESAMLPHP_SP_ASSERTION_CONSUMER_SERVICE",
                            value=f"{external_url}/multipass/saml/ubuntu/acs",
                        ),
                    ],
                )
            ],
        ),
    )
    v1.create_namespaced_pod(namespace=namespace, body=pod)
    service = kubernetes.client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=kubernetes.client.V1ObjectMeta(
            name=SIMPLESAMLPHP_SERVICE_NAME, namespace=namespace
        ),
        spec=kubernetes.client.V1ServiceSpec(
            type="ClusterIP",
            ports=[
                kubernetes.client.V1ServicePort(
                    port=SIMPLESAMLPHP_PORT,
                    target_port=SIMPLESAMLPHP_PORT,
                    name=f"tcp-{SIMPLESAMLPHP_PORT}",
                ),
            ],
            selector={"app.kubernetes.io/name": SIMPLESAMLPHP_POD_NAME},
        ),
    )
    v1.create_namespaced_service(namespace=namespace, body=service)
    deadline = time.time() + 300
    pod_ip = None
    while True:
        if time.time() > deadline:
            raise TimeoutError("timeout while waiting for simplesamlphp pod")
        try:
            pod = v1.read_namespaced_pod(name=SIMPLESAMLPHP_POD_NAME, namespace=namespace)
            if pod.status.phase == "Running":
                logger.info("simplesamlphp running at %s", pod.status.pod_ip)
                pod_ip = pod.status.pod_ip
                break
        except kubernetes.client.ApiException as exc:
            logger.debug("error reading simplesamlphp pod status: %s", exc)
        logger.info("waiting for simplesamlphp pod")
        time.sleep(1)
    return pod_ip


@pytest_asyncio.fixture(scope="module", name="saml_integrator")
async def saml_integrator_fixture(ops_test: OpsTest, app: Application, simplesamlphp_ip: str):
    """SAML integrator charm used for integration testing."""
    assert ops_test.model
    saml_config = {
        "entity_id": (
            f"http://{simplesamlphp_ip}:{SIMPLESAMLPHP_PORT}/simplesaml/saml2/idp/metadata.php"
        ),
        "metadata_url": (
            f"http://{simplesamlphp_ip}:{SIMPLESAMLPHP_PORT}/simplesaml/saml2/idp/metadata.php"
        ),
    }
    saml_integrator = await ops_test.model.deploy(
        "saml-integrator", channel="latest/stable", config=saml_config, trust=True
    )
    await ops_test.model.add_relation(app.name, saml_integrator.name)
    await ops_test.model.wait_for_idle(
        apps=[saml_integrator.name, app.name], status="active", raise_on_error=True
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
        apps=[s3_integrator.name], status="active", raise_on_error=True
    )
    await ops_test.model.add_relation(app.name, s3_integrator.name)
    await ops_test.model.wait_for_idle(
        apps=[s3_integrator.name, app.name], status="active", raise_on_error=True
    )
    yield s3_integrator


@pytest_asyncio.fixture(scope="module", name="loki")
async def loki_fixture(ops_test: OpsTest, app: Application):
    """Loki charm used for integration testing."""
    assert ops_test.model
    loki = await ops_test.model.deploy(
        "loki-k8s", channel="1/edge", trust=True, revision=97, series="focal"
    )
    await ops_test.model.add_relation(app.name, loki.name)
    await ops_test.model.wait_for_idle(
        apps=[loki.name, app.name], status="active", raise_on_error=True
    )
    yield loki
