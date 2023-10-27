# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""The SMTP relation observer."""
import logging

from charms.smtp_integrator.v0.smtp import SmtpDataAvailableEvent, SmtpRequires, TransportSecurity
from ops.charm import CharmBase
from ops.framework import Object

from state import SmtpConfig

logger = logging.getLogger(__name__)


class SmtpObserver(Object):
    """The SMTP integrator relation observer."""

    _RELATION_NAME = "smtp-legacy"

    def __init__(self, charm: CharmBase):
        """Initialize the observer and register event handlers.

        Args:
            charm: The parent charm to attach the observer to.
        """
        super().__init__(charm, "smtp-observer")
        self._charm = charm
        self.smtp = SmtpRequires(
            self._charm,
            relation_name=self._RELATION_NAME,
        )
        self.smtp_config = None
        self.framework.observe(
            self.smtp.on.smtp_data_available, self._saml_relation_data_available
        )

    def _saml_relation_data_available(self, event: SmtpDataAvailableEvent) -> None:
        """Handle the relation data available event.

        Args:
            event: the relation event.
        """
        self.smtp_config = SmtpConfig(
            host=event.host,
            port=event.port,
            login=event.user,
            password=event.password,
            use_tls=event.transport_security is not TransportSecurity.NONE,
        )
        self._charm.on.config_changed.emit()
