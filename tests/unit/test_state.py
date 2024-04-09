# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit tests."""

import unittest

import ops
import pytest
from charms.smtp_integrator.v0.smtp import AuthType, SmtpRelationData, TransportSecurity

import state


def test_proxyconfig_invalid(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched os.environ mapping that contains invalid proxy values.
    act: when charm state is initialized.
    assert: CharmConfigInvalidError is raised.
    """
    monkeypatch.setenv("JUJU_CHARM_HTTP_PROXY", "INVALID_URL")
    mock_charm = unittest.mock.MagicMock(spec=ops.CharmBase)
    mock_charm.config = {}

    with pytest.raises(state.CharmConfigInvalidError):
        state.State.from_charm(mock_charm, smtp_relation_data=None)


def test_config_from_charm_env(proxy_config: state.ProxyConfig):
    """
    arrange: given a monkeypatched os.environ with proxy configurations.
    act: when ProxyConfig.from_charm_config is called.
    assert: valid proxy configuration is returned.
    """
    mock_charm = unittest.mock.MagicMock(spec=ops.CharmBase)
    mock_charm.config = {}

    smtp_relation_data = SmtpRelationData(
        host="example.com",
        port=22,
        user="user",
        password="passwd",  # nosec
        transport_security=TransportSecurity.NONE,
        auth_type=AuthType.NONE,
    )
    config = state.State.from_charm(mock_charm, smtp_relation_data=smtp_relation_data)
    assert config.proxy_config, "Valid proxy config should not return None."
    assert config.proxy_config.http_proxy == proxy_config.http_proxy
    assert config.proxy_config.https_proxy == proxy_config.https_proxy
    assert config.proxy_config.no_proxy == proxy_config.no_proxy
    assert config.smtp_config.host == smtp_relation_data.host
    assert config.smtp_config.port == smtp_relation_data.port
    assert config.smtp_config.login == smtp_relation_data.user
    assert config.smtp_config.password == smtp_relation_data.password
    assert not config.smtp_config.use_tls
