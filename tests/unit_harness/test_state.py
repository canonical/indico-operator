# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit tests."""

from secrets import token_hex
from unittest.mock import MagicMock

import ops
import pytest
from charms.saml_integrator.v0.saml import SamlEndpoint, SamlRelationData
from charms.smtp_integrator.v0.smtp import AuthType, SmtpRelationData, TransportSecurity

import state


def test_proxyconfig_invalid(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched os.environ mapping that contains invalid proxy values.
    act: when charm state is initialized.
    assert: CharmConfigInvalidError is raised.
    """
    monkeypatch.setenv("JUJU_CHARM_HTTP_PROXY", "INVALID_URL")
    mock_charm = MagicMock(spec=ops.CharmBase)
    mock_charm.config = {}

    with pytest.raises(state.CharmConfigInvalidError):
        state.State.from_charm(mock_charm, smtp_relation_data=None)


def test_config_from_charm_env(proxy_config: state.ProxyConfig):
    """
    arrange: given a monkeypatched os.environ with proxy configurations.
    act: when ProxyConfig.from_charm_config is called.
    assert: valid proxy configuration is returned.
    """
    mock_charm = MagicMock(spec=ops.CharmBase)
    mock_charm.config = {}

    s3_relation_data = {
        "bucket": "sample-bucket",
        "endpoint": "s3.example.com",
        "access-key": token_hex(16),
        "secret-key": token_hex(16),
    }
    saml_endpoints = (
        SamlEndpoint(
            name="SingleSignOnService",
            url="https://example.com/login",
            binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
        ),
        SamlEndpoint(
            name="SingleLogoutService",
            url="https://example.com/logout",
            binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            response_url="https://example.com/response",
        ),
    )
    saml_relation_data = SamlRelationData(
        entity_id="entity",
        metadata_url="https://example.com/metadata",
        certificates=("cert1,", "cert2"),
        endpoints=saml_endpoints,
    )
    smtp_relation_data = SmtpRelationData(
        host="example.com",
        port=22,
        user="user",
        password=token_hex(16),
        transport_security=TransportSecurity.NONE,
        auth_type=AuthType.NONE,
    )
    config = state.State.from_charm(
        mock_charm,
        s3_relation_data=s3_relation_data,
        saml_relation_data=saml_relation_data,
        smtp_relation_data=smtp_relation_data,
    )

    assert config.proxy_config, "Valid proxy config should not return None."
    assert config.proxy_config.http_proxy == proxy_config.http_proxy
    assert config.proxy_config.https_proxy == proxy_config.https_proxy
    assert config.proxy_config.no_proxy == proxy_config.no_proxy
    assert config.s3_config.bucket == s3_relation_data["bucket"]
    assert config.s3_config.host == s3_relation_data["endpoint"]
    assert config.s3_config.access_key == s3_relation_data["access-key"]
    assert config.s3_config.secret_key == s3_relation_data["secret-key"]
    assert config.saml_config.entity_id == saml_relation_data.entity_id
    assert config.saml_config.metadata_url == saml_relation_data.metadata_url
    assert config.saml_config.certificates == saml_relation_data.certificates
    assert config.saml_config.endpoints[0].name == saml_relation_data.endpoints[0].name
    assert config.saml_config.endpoints[0].url == saml_relation_data.endpoints[0].url
    assert config.saml_config.endpoints[0].binding == saml_relation_data.endpoints[0].binding
    assert config.saml_config.endpoints[1].name == saml_relation_data.endpoints[1].name
    assert config.saml_config.endpoints[1].url == saml_relation_data.endpoints[1].url
    assert config.saml_config.endpoints[1].binding == saml_relation_data.endpoints[1].binding
    assert config.saml_config.endpoints[1].response_url == (
        saml_relation_data.endpoints[1].response_url
    )
    assert config.smtp_config.host == smtp_relation_data.host
    assert config.smtp_config.port == smtp_relation_data.port
    assert config.smtp_config.login == smtp_relation_data.user
    assert config.smtp_config.password == smtp_relation_data.password
    assert not config.smtp_config.use_tls


def test_s3_config_get_connection_string():
    """
    arrange: create an S3Config object.
    act: call the get_connection_string method.
    assert: the returned value matches the object attributes.
    """
    access_key = token_hex(16)
    secret_key = token_hex(16)
    s3_config = state.S3Config(
        bucket="sample-bucket",
        host="s3.example.com",
        access_key=access_key,
        secret_key=secret_key,
    )

    connection_string = s3_config.get_connection_string()

    assert connection_string == (
        f"s3:bucket=sample-bucket,access_key={access_key},"
        f"secret_key={secret_key},proxy=true,host=s3.example.com"
    )


def test_s3_config_get_connection_string_without_host():
    """
    arrange: create an S3Config object.
    act: call the get_connection_string method.
    assert: the returned value matches the object attributes.
    """
    access_key = token_hex(16)
    secret_key = token_hex(16)
    s3_config = state.S3Config(
        bucket="sample-bucket",
        access_key=access_key,
        secret_key=secret_key,
    )

    connection_string = s3_config.get_connection_string()

    assert connection_string == (
        f"s3:bucket=sample-bucket,access_key={access_key},secret_key={secret_key},proxy=true"
    )
