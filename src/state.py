# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Indico states."""

import dataclasses
import logging
import os
from typing import Dict, List, Optional, Tuple

import ops
from charms.saml_integrator.v0.saml import SamlRelationData
from charms.smtp_integrator.v0.smtp import SmtpRelationData, TransportSecurity

# pylint: disable=no-name-in-module
from pydantic import AnyHttpUrl, BaseModel, Field, HttpUrl, ValidationError

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


class S3Config(BaseModel):  # pylint: disable=too-few-public-methods
    """S3 configuration.

    Attributes:
        bucket: the S3 bucket.
        host: S3 host.
        access_key: S3 access key.
        secret_key: S3 secret key.
    """

    bucket: str
    host: Optional[str]
    access_key: str
    secret_key: str

    def get_connection_string(self) -> str:
        """Retrieve a connection string for this instance.

        Returns: the connection string for this instance.
        """
        connection_string = (
            f"s3:bucket={self.bucket},access_key={self.access_key},"
            f"secret_key={self.secret_key},proxy=true"
        )
        if self.host:
            connection_string = f"{connection_string},host={self.host}"
        return connection_string


class SamlEndpoint(BaseModel):  # pylint: disable=too-few-public-methods
    """SAML configuration.

    Attributes:
        name: Endpoint name.
        url: Endpoint URL.
        binding: Endpoint binding.
        response_url: URL to address the response to.
    """

    name: str = Field(..., min_length=1)
    url: AnyHttpUrl
    binding: str = Field(..., min_length=1)
    response_url: Optional[AnyHttpUrl]


class SamlConfig(BaseModel):  # pylint: disable=too-few-public-methods
    """SAML configuration.

    Attributes:
        entity_id: SAML entity ID.
        metadata_url: Metadata URL.
        certificates: List of x509 certificates.
        endpoints: List of endpoints.
    """

    entity_id: str = Field(..., min_length=1)
    metadata_url: AnyHttpUrl
    certificates: Tuple[str, ...]
    endpoints: Tuple[SamlEndpoint, ...]


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
        saml_config: SAML configuration.
        smtp_config: SMTP configuration.
        s3_config: S3 configuration.
    """

    proxy_config: Optional[ProxyConfig]
    saml_config: Optional[SamlConfig]
    smtp_config: Optional[SmtpConfig]
    s3_config: Optional[S3Config]

    # pylint: disable=unused-argument
    @classmethod
    def from_charm(
        cls,
        charm: ops.CharmBase,
        s3_relation_data: Optional[Dict[str, str]] = None,
        saml_relation_data: Optional[SamlRelationData] = None,
        smtp_relation_data: Optional[SmtpRelationData] = None,
    ) -> "State":
        """Initialize the state from charm.

        Args:
            charm: The charm root IndicoOperatorCharm.
            s3_relation_data: S3 relation data.
            saml_relation_data: SAML relation data.
            smtp_relation_data: SMTP relation data.

        Returns:
            Current state of Indico.

        Raises:
            CharmConfigInvalidError: if invalid state values were encountered.
        """
        try:
            saml_config = None
            if saml_relation_data:
                endpoints: List[SamlEndpoint] = []
                for endpoint in saml_relation_data.endpoints:
                    endpoints.append(
                        SamlEndpoint(
                            name=endpoint.name,
                            url=endpoint.url,
                            binding=endpoint.binding,
                            response_url=endpoint.response_url,
                        )
                    )
                saml_config = SamlConfig(
                    entity_id=saml_relation_data.entity_id,
                    metadata_url=saml_relation_data.metadata_url,
                    certificates=saml_relation_data.certificates,
                    endpoints=tuple(endpoints),
                )
            proxy_config = ProxyConfig.from_env()
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
            s3_config = (
                S3Config(
                    bucket=s3_relation_data["bucket"],
                    host=s3_relation_data["endpoint"],
                    access_key=s3_relation_data["access-key"],
                    secret_key=s3_relation_data["secret-key"],
                )
                if s3_relation_data and "access-key" in s3_relation_data
                else None
            )
        except ValidationError as exc:
            logger.error("Invalid juju model proxy configuration, %s", exc)
            raise CharmConfigInvalidError("Invalid model proxy configuration.") from exc
        return cls(
            proxy_config=proxy_config,
            smtp_config=smtp_config,
            saml_config=saml_config,
            s3_config=s3_config,
        )
