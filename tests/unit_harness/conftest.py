# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""Fixtures for unit tests."""

from secrets import token_hex

import pytest

import state


@pytest.fixture(scope="function", name="proxy_config")
def proxy_config_fixture(monkeypatch: pytest.MonkeyPatch):
    """Proxy configuration with authentication and no_proxy values."""
    # Mypy doesn't understand str is supposed to be converted to HttpUrl by Pydantic.
    proxy_config = state.ProxyConfig(
        http_proxy=f"http://testusername:{token_hex(16)}@httptest.internal:3127",  # type: ignore
        https_proxy=f"http://testusername:{token_hex(16)}@httpstest.internal:3127",  # type: ignore
        no_proxy="noproxy.host1,noproxy.host2",
    )
    monkeypatch.setattr(
        state.os,
        "environ",
        {
            "JUJU_CHARM_HTTP_PROXY": str(proxy_config.http_proxy),
            "JUJU_CHARM_HTTPS_PROXY": str(proxy_config.https_proxy),
            "JUJU_CHARM_NO_PROXY": str(proxy_config.no_proxy),
        },
    )
    return proxy_config
