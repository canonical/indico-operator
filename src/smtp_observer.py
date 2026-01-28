# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""The SMTP relation observer."""

import logging

from charms.smtp_integrator.v0.smtp import SmtpRequires
from ops.charm import CharmBase
from ops.framework import Object

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
            self.smtp.on.smtp_data_available, self._on_smtp_relation_data_available
        )

    def _on_smtp_relation_data_available(self, _) -> None:
        """Handle the relation data available event."""
        # A config changed is emitted to avoid a huge refactor at this point.
        self._charm.on.config_changed.emit()
