# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Indico states."""
import dataclasses
import logging
import os
import typing

import ops
from pydantic import BaseModel, HttpUrl, ValidationError  # pylint: disable=no-name-in-module

logger = logging.getLogger(__name__)


class CharmStateBaseError(Exception):
    """Represents an error with charm state."""


class CharmConfigInvalidError(CharmStateBaseError):
    """Exception raised when a charm configuration is found to be invalid.

    Attributes:
        msg: Explanation of the error.
    """

    def __init__(self, msg: str):
        """Initialize a new instance of the CharmConfigInvalidError exception.

        Args:
            msg: Explanation of the error.
        """
        self.msg = msg


class ProxyConfig(BaseModel):  # pylint: disable=too-few-public-methods
    """Configuration for accessing Indico through proxy.

    Attributes:
        http_proxy: The http proxy URL.
        https_proxy: The https proxy URL.
        no_proxy: Comma separated list of hostnames to bypass proxy.
    """

    http_proxy: typing.Optional[HttpUrl]
    https_proxy: typing.Optional[HttpUrl]
    no_proxy: typing.Optional[str]

    @classmethod
    def from_env(cls) -> typing.Optional["ProxyConfig"]:
        """Instantiate ProxyConfig from juju charm environment.

        Returns:
            ProxyConfig if proxy configuration is provided, None otherwise.
        """
        http_proxy = os.environ.get("JUJU_CHARM_HTTP_PROXY")
        https_proxy = os.environ.get("JUJU_CHARM_HTTPS_PROXY")
        no_proxy = os.environ.get("JUJU_CHARM_NO_PROXY")
        if not http_proxy and not https_proxy:
            return None
        # Mypy doesn't understand str is supposed to be converted to HttpUrl by Pydantic.
        return cls(
            http_proxy=http_proxy, https_proxy=https_proxy, no_proxy=no_proxy  # type: ignore
        )


@dataclasses.dataclass(frozen=True)
class State:  # pylint: disable=too-few-public-methods
    """The Indico operator charm state.

    Attributes:
        proxy_config: Proxy configuration.
    """

    proxy_config: typing.Optional[ProxyConfig]

    @classmethod
    def from_charm(cls, charm: ops.CharmBase) -> "State":  # pylint: disable=unused-argument
        """Initialize the state from charm.

        Args:
            charm: The charm root IndicoOperatorCharm.

        Returns:
            Current state of Indico.

        Raises:
            CharmConfigInvalidError: if invalid state values were encountered.
        """
        try:
            proxy_config = ProxyConfig.from_env()
        except ValidationError as exc:
            logger.error("Invalid juju model proxy configuration, %s", exc)
            raise CharmConfigInvalidError("Invalid model proxy configuration.") from exc
        return cls(proxy_config=proxy_config)
