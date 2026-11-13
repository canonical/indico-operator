# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Regression tests for integration setup without deploying Juju applications."""

import json
from pathlib import Path
from secrets import token_hex
from unittest.mock import Mock

import pytest

from integration import conftest

pytest_plugins = ["pytester"]


def test_integration_options(pytester: pytest.Pytester):
    pytester.syspathinsert(Path(__file__).parent)
    pytester.makeconftest("from integration.conftest import pytest_addoption")
    pytester.makepyfile(
        """
        def test_options(pytestconfig):
            assert pytestconfig.getoption("--s3-address") == "127.0.0.1"
            assert pytestconfig.getoption("--no-juju-teardown")
            assert pytestconfig.getoption("--juju-model") == "indico-test"
        """
    )
    result = pytester.runpytest(
        "--s3-address", "127.0.0.1", "--no-juju-teardown", "--juju-model", "indico-test"
    )
    result.assert_outcomes(passed=1)


def test_module_fixture_scopes(pytester: pytest.Pytester):
    pytester.syspathinsert(Path(__file__).parent)
    pytester.makeconftest("from integration.conftest import app_fixture, indico_address")
    pytester.makepyfile(
        """
        def test_scope(indico_address):
            pass
        """
    )
    result = pytester.runpytest("--setup-plan")
    assert result.ret == pytest.ExitCode.OK
    result.stdout.fnmatch_lines(["*SETUP*M app*", "*SETUP*M indico_address*"])


def test_s3_address_override():
    config = Mock()
    config.getoption.return_value = "192.0.2.10"
    assert conftest.s3_address.__wrapped__(config) == "192.0.2.10"


def test_s3_address_unavailable(monkeypatch: pytest.MonkeyPatch):
    config = Mock()
    config.getoption.return_value = None
    monkeypatch.setattr(conftest, "_host_ip", lambda: None)
    with pytest.raises(pytest.fail.Exception, match="pass --s3-address"):
        conftest.s3_address.__wrapped__(config)


def test_missing_s3_identity(tmp_path: Path):
    config = Mock(rootpath=tmp_path)
    with pytest.raises(pytest.fail.Exception, match="prepare-s3.sh"):
        conftest.s3_config.__wrapped__("127.0.0.1", config)


def test_s3_bucket_setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    build = tmp_path / "build"
    build.mkdir()
    credentials = {"access_key": token_hex(8), "secret_key": token_hex(16)}
    (build / "s3-user.json").write_text(json.dumps({"keys": [credentials]}))
    client_factory = Mock()
    monkeypatch.setattr(conftest.boto3, "client", client_factory)

    config = conftest.s3_config.__wrapped__("127.0.0.1", Mock(rootpath=tmp_path))

    assert config["endpoint"] == "http://127.0.0.1:7480"
    assert config["access-key"] == credentials["access_key"]
    assert config["secret-key"] == credentials["secret_key"]
    assert client_factory.call_args.kwargs["endpoint_url"] == config["endpoint"]
    client_factory.return_value.create_bucket.assert_called_once_with(Bucket="indico-test")
    client_factory.return_value.head_bucket.assert_called_once_with(Bucket="indico-test")


def test_s3_bucket_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    build = tmp_path / "build"
    build.mkdir()
    (build / "s3-user.json").write_text(
        json.dumps({"keys": [{"access_key": token_hex(8), "secret_key": token_hex(16)}]})
    )
    client_factory = Mock()
    client_factory.return_value.head_bucket.side_effect = RuntimeError("bucket unavailable")
    monkeypatch.setattr(conftest.boto3, "client", client_factory)

    with pytest.raises(RuntimeError, match="bucket unavailable"):
        conftest.s3_config.__wrapped__("127.0.0.1", Mock(rootpath=tmp_path))
