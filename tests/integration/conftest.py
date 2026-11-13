# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for Indico charm integration tests."""

import json
import logging
import socket
from pathlib import Path

import boto3
import jubilant
import pytest
from botocore.config import Config

logger = logging.getLogger(__name__)

# Timeout for juju wait operations in seconds
JUJU_WAIT_TIMEOUT = 1200

APP_NAME = "indico"

# The flask-framework workload (gunicorn) and its Kubernetes service both
# listen on port 8000; paas-charm uses this fixed port regardless of the
# extension's documented default.
WORKLOAD_PORT = 8000

def pytest_addoption(parser: pytest.Parser) -> None:
    """Register project-specific integration test options."""
    parser.addoption("--s3-address", action="store", help="S3 service host address")


@pytest.fixture(scope="module", name="app")
def app_fixture(
    juju: jubilant.Juju,
    charm_path: str,
    resource_images: dict[str, str],
):
    """Deploy the Indico charm and its mandatory relations.

    Deploys postgresql-k8s and redis-k8s, the indico charm, integrates them,
    and waits for all units to become active.
    """
    juju.wait_timeout = JUJU_WAIT_TIMEOUT
    # Detect Juju major version to choose the right PostgreSQL channel
    juju_major = juju.version().major

    if juju_major >= 4:
        pg_channel = "16/edge"
        pg_base = "ubuntu@24.04"
        is_force = True
    else:
        pg_channel = "14/stable"
        pg_base = "ubuntu@22.04"
        is_force = False

    # Deploy PostgreSQL
    juju.deploy(
        "postgresql-k8s",
        channel=pg_channel,
        base=pg_base,
        trust=True,
        config={
            "profile": "testing",
            "plugin_pg_trgm_enable": "true",
            "plugin_unaccent_enable": "true",
        },
        force=is_force,
    )

    # Deploy Redis
    juju.deploy("redis-k8s", channel="latest/edge", trust=True)

    juju.wait(
        lambda status: jubilant.all_active(status, "postgresql-k8s", "redis-k8s"),
        timeout=JUJU_WAIT_TIMEOUT,
    )

    # Deploy the Indico charm
    juju.deploy(
        charm_path,
        app=APP_NAME,
        resources=resource_images,
    )
    juju.wait(lambda status: jubilant.all_waiting(status, APP_NAME))

    # Integrate with the mandatory backing services
    juju.integrate(APP_NAME, "postgresql-k8s:database")
    juju.integrate(APP_NAME, "redis-k8s")
    juju.wait(jubilant.all_active, timeout=JUJU_WAIT_TIMEOUT)

    # Indico builds its URL map from BASE_URL and returns HTTP 404 for every
    # route whose request host does not match it. When neither `site_url` nor
    # an ingress relation is set, BASE_URL falls back to `http://localhost`,
    # so tests reaching the workload by pod IP would get 404s. Point
    # `site_url` at the address the tests actually use (pod IP + workload
    # port) so Indico serves normally over direct HTTP.
    status = juju.status()
    unit_address = status.apps[APP_NAME].units[f"{APP_NAME}/0"].address
    juju.config(APP_NAME, {"site_url": f"http://{unit_address}:{WORKLOAD_PORT}"})
    juju.wait(jubilant.all_active, timeout=JUJU_WAIT_TIMEOUT)

    yield APP_NAME


@pytest.fixture(scope="module")
def indico_address(app: str, juju: jubilant.Juju) -> str:
    """Get the Indico address.

    Uses the unit (pod) IP and the workload port. The application ClusterIP
    is deliberately avoided: on microk8s the ClusterIP range is not routable
    from the test host, whereas Calico pod IPs are. The port must be the
    workload port (8000) that gunicorn binds, not the extension's documented
    default.
    """
    status = juju.status()
    address = status.apps[app].units[app + "/0"].address or status.apps[app].address
    return f"http://{address}:{WORKLOAD_PORT}"


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Pytest hook to set the test rep_* attribute for abort_on_fail."""
    _ = call
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(autouse=True)
def abort_on_fail(request: pytest.FixtureRequest):
    """Fixture which aborts other tests in module after first fails."""
    abort_on_fail = request.node.get_closest_marker("abort_on_fail")
    if abort_on_fail and getattr(request.module, "__aborted__", False):
        pytest.xfail("abort_on_fail")
    _ = yield
    if abort_on_fail and request.node.rep_call.failed:
        request.module.__aborted__ = True


def _host_ip() -> str | None:
    """Return the host's primary outbound IP, reachable from microk8s pods."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return None


@pytest.fixture(scope="session")
def s3_address(pytestconfig: pytest.Config) -> str:
    """Provide the S3 service IP address for integration tests."""
    address = pytestconfig.getoption("--s3-address") or _host_ip()
    if not address:
        pytest.fail("Cannot determine the S3 service address; pass --s3-address.")
    return address


@pytest.fixture(scope="session")
def s3_config(s3_address: str, pytestconfig: pytest.Config) -> dict[str, str]:
    """Create and verify the S3 bucket using the provisioned test identity."""
    user_path = Path(pytestconfig.rootpath) / "build" / "s3-user.json"
    if not user_path.is_file():
        pytest.fail("S3 test identity is missing; run bash tests/integration/prepare-s3.sh.")
    user = json.loads(user_path.read_text())
    credentials = user["keys"][0]
    config = {
        "access-key": credentials["access_key"],
        "secret-key": credentials["secret_key"],
        "bucket": "indico-test",
        "region": "us-east-1",
        "path": "indico",
        "endpoint": f"http://{s3_address}:7480",
    }
    client = boto3.client(
        "s3",
        endpoint_url=config["endpoint"],
        region_name=config["region"],
        aws_access_key_id=config["access-key"],
        aws_secret_access_key=config["secret-key"],
        config=Config(
            s3={"addressing_style": "path"},
            connect_timeout=10,
            read_timeout=10,
            retries={"max_attempts": 3},
        ),
    )
    client.create_bucket(Bucket=config["bucket"])
    client.head_bucket(Bucket=config["bucket"])
    return config
