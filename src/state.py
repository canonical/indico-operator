# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Indico states."""
import dataclasses
import logging
import os
from typing import Optional

import ops
from charms.saml_integrator.v0 import saml
from charms.smtp_integrator.v0.smtp import SmtpRelationData, TransportSecurity

# pylint: disable=no-name-in-module
from pydantic import BaseModel, Field, HttpUrl, ValidationError

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

    http_proxy: Optional[HttpUrl]
    https_proxy: Optional[HttpUrl]
    no_proxy: Optional[str]

    @classmethod
    def from_env(cls) -> Optional["ProxyConfig"]:
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


class SmtpConfig(BaseModel):  # pylint: disable=too-few-public-methods
    """SMTP configuration.

    Attributes:
        login: SMTP user.
        password: SMTP passwaord.
        port: SMTP port.
        host: SMTP host.
        use_tls: whether TLS is enabled.
    """

    login: Optional[str]
    password: Optional[str]
    port: int = Field(None, ge=1, le=65536)
    host: str = Field(..., min_length=1)
    use_tls: bool


@dataclasses.dataclass()
class State:  # pylint: disable=too-few-public-methods
    """The Indico operator charm state.

    Attributes:
        proxy_config: Proxy configuration.
        smtp_config: SMTP configuration.
    """

    proxy_config: Optional[ProxyConfig]
    saml_config: Optional[SamlRelationData]
    smtp_config: Optional[SmtpConfig]

    # pylint: disable=unused-argument
    @classmethod
    def from_charm(
        cls,
        charm: ops.CharmBase,
        saml_relation_data: Optional[saml.SamlRelationData],
        smtp_relation_data: Optional[SmtpRelationData],
    ) -> "State":
        """Initialize the state from charm.

        Args:
            charm: The charm root IndicoOperatorCharm.
            smtp_relation_data: SMTP relation data.

        Returns:
            Current state of Indico.

        Raises:
            CharmConfigInvalidError: if invalid state values were encountered.
        """
        try:
            proxy_config = ProxyConfig.from_env()
            saml_config = (
                entity_id
            )
            smtp_config = (
                SmtpConfig(
                    host=smtp_relation_data.host,
                    port=smtp_relation_data.port,
                    login=smtp_relation_data.user,
                    password=smtp_relation_data.password,
                    use_tls=smtp_relation_data.transport_security is not TransportSecurity.NONE,
                )
                if smtp_relation_data
                else None
            )
        except ValidationError as exc:
            logger.error("Invalid juju model proxy configuration, %s", exc)
            raise CharmConfigInvalidError("Invalid model proxy configuration.") from exc
        return cls(proxy_config=proxy_config, smtp_config=smtp_config)
