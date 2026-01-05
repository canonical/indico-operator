# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.

"""The S3 agent relation observer."""
import logging

from charms.data_platform_libs.v0.s3 import S3Requirer
from ops.charm import CharmBase
from ops.framework import Object

logger = logging.getLogger(__name__)


class S3Observer(Object):
    """The S3 integrator relation observer."""

    _RELATION_NAME = "s3"

    def __init__(self, charm: CharmBase):
        """Initialize the observer and register event handlers.

        Args:
            charm: The parent charm to attach the observer to.
        """
        super().__init__(charm, "s3-observer")
        self._charm = charm
        self.s3 = S3Requirer(
            self._charm,
            relation_name=self._RELATION_NAME,
        )
        self.framework.observe(self.s3.on.credentials_changed, self._on_credentials_changed)
        self.framework.observe(self.s3.on.credentials_gone, self._on_credentials_gone)

    def _on_credentials_changed(self, _) -> None:
        """Handle the credentials changed event."""
        # A config changed is emitted to avoid a huge refactor at this point.
        self._charm.on.config_changed.emit()

    def _on_credentials_gone(self, _) -> None:
        """Handle the credentials gone event."""
        # A config changed is emitted to avoid a huge refactor at this point.
        self._charm.on.config_changed.emit()
