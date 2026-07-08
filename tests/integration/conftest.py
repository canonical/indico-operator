# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for Indico charm integration tests."""

import logging
import socket
import typing
from collections.abc import Generator

import jubilant
import pytest

logger = logging.getLogger(__name__)

# Timeout for juju wait operations in seconds
JUJU_WAIT_TIMEOUT = 1200

APP_NAME = "indico"

# The flask-framework workload (gunicorn) and its Kubernetes service both
# listen on port 8000; paas-charm uses this fixed port regardless of the
# extension's documented default.
WORKLOAD_PORT = 8000


@pytest.fixture(scope="session", name="charm")
def charm_fixture(pytestconfig: pytest.Config):
    """Get value from parameter charm-file."""
    charm = pytestconfig.getoption("--charm-file")
    use_existing = pytestconfig.getoption("--use-existing", default=False)
    if not use_existing:
        assert charm, "--charm-file must be set"
    return charm


@pytest.fixture(scope="session")
def charm_resources(pytestconfig: pytest.Config) -> dict[str, str]:
    """The OCI resources for the charm."""
    rock_image_uri = pytestconfig.getoption("--indico-image")
    if not rock_image_uri:
        pytest.fail("--indico-image must be set")

    return {"flask-app-image": rock_image_uri}


@pytest.fixture(scope="session", name="juju")
def juju_fixture(
    request: pytest.FixtureRequest,
) -> Generator[jubilant.Juju, None, None]:
    """Pytest fixture that wraps :meth:`jubilant.with_model`."""

    def show_debug_log(juju: jubilant.Juju):
        """Show debug log.

        Args:
            juju: the Juju object.
        """
        if request.session.testsfailed:
            log = juju.debug_log(limit=1000)
            print(log, end="")

    use_existing = request.config.getoption("--use-existing", default=False)
    if use_existing:
        juju = jubilant.Juju()
        yield juju
        show_debug_log(juju)
        return

    model = request.config.getoption("--model")
    if model:
        juju = jubilant.Juju(model=model)
        yield juju
        show_debug_log(juju)
        return

    keep_models = typing.cast(bool, request.config.getoption("--keep-models"))
    with jubilant.temp_model(keep=keep_models) as juju:
        juju.wait_timeout = JUJU_WAIT_TIMEOUT
        yield juju
        show_debug_log(juju)
        return


@pytest.fixture(scope="session", name="app")
def app_fixture(
    juju: jubilant.Juju,
    charm: str,
    charm_resources: dict[str, str],
):
    """Deploy the Indico charm and its mandatory relations.

    Deploys postgresql-k8s and redis-k8s, the indico charm, integrates them,
    and waits for all units to become active.
    """
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
        charm=charm,
        app=APP_NAME,
        resources=charm_resources,
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


@pytest.fixture(scope="session")
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
def s3_address(pytestconfig: pytest.Config) -> str | None:
    """Provide the S3 service IP address for integration tests."""
    return pytestconfig.getoption("--s3-address") or _host_ip()


def generate_s3_config(s3_address: str) -> dict:
    """Generate S3 config for the integration tests."""
    return {
        "access-key": "my-lovely-key",
        "secret-key": "this-is-very-secret",
        "bucket": "indico-test",
        "region": "us-east-1",
        "path": "indico",
        "endpoint": f"http://{s3_address}:7480",
    }
