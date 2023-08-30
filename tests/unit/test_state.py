# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Unit tests."""

import unittest

import ops
import pytest

import state


def test_proxyconfig_invalid(monkeypatch: pytest.MonkeyPatch):
    """
    arrange: given a monkeypatched os.environ mapping that contains invalid proxy values.
    act: when charm state is initialized.
    assert: CharmConfigInvalidError is raised.
    """
    monkeypatch.setattr(state.os, "environ", {"JUJU_CHARM_HTTP_PROXY": "INVALID_URL"})
    mock_charm = unittest.mock.MagicMock(spec=ops.CharmBase)
    mock_charm.config = {}

    with pytest.raises(state.CharmConfigInvalidError):
        state.State.from_charm(mock_charm)


def test_proxyconfig_from_charm_env(proxy_config: state.ProxyConfig):
    """
    arrange: given a monkeypatched os.environ with proxy configurations.
    act: when ProxyConfig.from_charm_config is called.
    assert: valid proxy configuration is returned.
    """
    mock_charm = unittest.mock.MagicMock(spec=ops.CharmBase)
    mock_charm.config = {}

    config = state.State.from_charm(mock_charm).proxy_config
    assert config, "Valid proxy config should not return None."
    assert config.http_proxy == proxy_config.http_proxy
    assert config.https_proxy == proxy_config.https_proxy
    assert config.no_proxy == proxy_config.no_proxy
