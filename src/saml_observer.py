# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""The SAML relation observer."""
import logging

from charms.saml_integrator.v0.saml import SamlRequires
from ops.charm import CharmBase
from ops.framework import Object

logger = logging.getLogger(__name__)


class SamlObserver(Object):
    """The SMTP integrator relation observer."""

    _RELATION_NAME = "saml"

    def __init__(self, charm: CharmBase):
        """Initialize the observer and register event handlers.

        Args:
            charm: The parent charm to attach the observer to.
        """
        super().__init__(charm, "saml-observer")
        self._charm = charm
        self.saml = SamlRequires(
            self._charm,
            relation_name=self._RELATION_NAME,
        )
        self.framework.observe(
            self.saml.on.saml_data_available, self._on_saml_relation_data_available
        )

    def _on_saml_relation_data_available(self, _) -> None:
        """Handle the relation data available event."""
        # A config changed is emitted to avoid a huge refactor at this point.
        self._charm.on.config_changed.emit()
