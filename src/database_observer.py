# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""The Database agent relation observer."""
import logging
import typing

from charms.data_platform_libs.v0.data_interfaces import (
    DatabaseCreatedEvent,
    DatabaseEndpointsChangedEvent,
    DatabaseRequires,
)
from ops.charm import CharmBase
from ops.framework import Object

logger = logging.getLogger(__name__)


class DatabaseObserver(Object):
    """The Database relation observer.

    Attrs:
        uri: The database uri.
    """

    _RELATION_NAME = "database"
    # SUPERUSER is required for the schema migrations
    _DATABASE_USER = "SUPERUSER"

    def __init__(self, charm: CharmBase):
        """Initialize the observer and register event handlers.

        Args:
            charm: The parent charm to attach the observer to.
        """
        super().__init__(charm, "database-observer")
        self._charm = charm
        self.database = DatabaseRequires(
            self._charm,
            relation_name=self._RELATION_NAME,
            database_name=self._charm.app.name,
            extra_user_roles=self._DATABASE_USER,
        )
        self.framework.observe(self.database.on.database_created, self._on_database_created)
        self.framework.observe(self.database.on.endpoints_changed, self._on_endpoints_changed)

    def _on_database_created(self, _: DatabaseCreatedEvent) -> None:
        """Handle database created."""
        self._charm.on.config_changed.emit()

    def _on_endpoints_changed(self, _: DatabaseEndpointsChangedEvent) -> None:
        """Handle endpoints change."""
        self._charm.on.config_changed.emit()

    @property
    def uri(self) -> typing.Optional[str]:
        """Get the database uri from the relation data.

        Returns:
            str: The uri.
        """
        if self.model.get_relation(self._RELATION_NAME) is None or not self.database.relations:
            return None

        relation_id = self.database.relations[0].id
        relation_data = self.database.fetch_relation_data().get(relation_id, {})
        user = relation_data.get("username", "")
        password = relation_data.get("password", "")
        database = relation_data.get("database", "")
        endpoint = relation_data.get("endpoints", "").split(",")[0]
        if not user or not password or not database or not endpoint:
            return None
        return f"postgresql://{user}:{password}@{endpoint}/{database}"
