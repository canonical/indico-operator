# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""# Interface Library for OpenFGA.

> **DEPRECATED**
> This charm library is deprecated in favor of the `charmlibs-interfaces-openfga` PyPI package.
> Please install `charmlibs-interfaces-openfga` and import from `charmlibs.interfaces.openfga`.

This library wraps relation endpoints using the `openfga` interface
and provides a Python API for requesting OpenFGA authorization model
stores to be created.

## Getting Started

To get started using the library, you just need to fetch the library using `charmcraft`.

```shell
cd some-charm
charmcraft fetch-lib charms.openfga_k8s.v1.openfga
```

In the `metadata.yaml` of the charm, add the following:

```yaml
requires:
  openfga:
    interface: openfga
```

Then, to initialise the library:
```python
from charms.openfga_k8s.v1.openfga import (
    OpenFGARequires,
    OpenFGAStoreCreateEvent,
)

class SomeCharm(CharmBase):
  def __init__(self, *args):
    # ...
    self.openfga = OpenFGARequires(self, "test-openfga-store")
    self.framework.observe(
        self.openfga.on.openfga_store_created,
        self._on_openfga_store_created,
    )

    def _on_openfga_store_created(self, event: OpenFGAStoreCreateEvent):
        if not event.store_id:
            return

        info = self.openfga.get_store_info()
        if not info:
            return

        logger.info("store id {}".format(info.store_id))
        logger.info("token {}".format(info.token))
        logger.info("grpc_api_url {}".format(info.grpc_api_url))
        logger.info("http_api_url {}".format(info.http_api_url))

```
"""

import logging
from typing import Optional

import pydantic
from ops import (
    Application,
    CharmBase,
    Handle,
    HookEvent,
    Relation,
    RelationCreatedEvent,
    RelationDepartedEvent,
    TooManyRelatedAppsError,
)
from ops.charm import CharmEvents, RelationChangedEvent, RelationEvent
from ops.framework import EventSource, Object
from pydantic import BaseModel, Field

# The unique Charmhub library identifier, never change it
LIBID = "216f28cfeea4447b8a576f01bfbecdf5"

# Increment this major API version when introducing breaking changes
LIBAPI = 1

# Increment this PATCH version before using `charmcraft publish-lib` or reset
# to 0 if you are raising the major API version
LIBPATCH = 6

PYDEPS = ["pydantic ~= 2.0"]

logger = logging.getLogger(__name__)

DEFAULT_INTEGRATION_NAME = "openfga"


def _update_relation_app_databag(app: Application, relation: Relation, data: dict) -> None:
    if relation is None:
        return

    data = {k: str(v) if v else "" for k, v in data.items()}
    relation.data[app].update(data)


class OpenfgaRequirerAppData(BaseModel):
    """Openfga requirer application databag model."""

    store_name: str = Field(description="The store name the application requires")


class OpenfgaProviderBaseData(BaseModel):
    """Openfga provider base application databag model."""

    grpc_api_url: str = Field(description="The openfga server GRPC address")
    http_api_url: str = Field(description="The openfga server HTTP address")


class OpenfgaProviderAppData(OpenfgaProviderBaseData):
    """Openfga requirer application databag model."""

    store_id: Optional[str] = Field(description="The store_id", default=None)
    token: Optional[str] = Field(description="The API token", default=None, exclude=True)
    token_secret_id: Optional[str] = Field(
        description="The juju secret_id which can be used to retrieve the API token",
        default=None,
    )


class OpenFGAStoreCreateEvent(HookEvent):
    """Event emitted when a new OpenFGA store is created."""

    def __init__(self, handle: Handle, store_id: str):
        super().__init__(handle)
        self.store_id = store_id

    def snapshot(self) -> dict:
        """Save event."""
        return {
            "store_id": self.store_id,
        }

    def restore(self, snapshot: dict) -> None:
        """Restore event."""
        self.store_id = snapshot["store_id"]


class OpenFGAStoreRemovedEvent(HookEvent):
    """Event emitted when a new OpenFGA store is removed."""


class OpenFGARequirerEvents(CharmEvents):
    """Custom charm events."""

    openfga_store_created = EventSource(OpenFGAStoreCreateEvent)
    openfga_store_removed = EventSource(OpenFGAStoreRemovedEvent)


class OpenFGARequires(Object):
    """This class defines the functionality for the 'requires' side of the 'openfga' relation.

    Hook events observed:
        - relation-created
        - relation-changed
        - relation-departed
    """

    on = OpenFGARequirerEvents()

    def __init__(
        self,
        charm: CharmBase,
        store_name: str,
        relation_name: str = DEFAULT_INTEGRATION_NAME,
    ) -> None:
        super().__init__(charm, relation_name)
        self.charm = charm
        self.app = charm.app
        self.relation_name = relation_name
        self.store_name = store_name

        self.framework.observe(charm.on[relation_name].relation_created, self._on_relation_created)
        self.framework.observe(
            charm.on[relation_name].relation_changed,
            self._on_relation_changed,
        )
        self.framework.observe(
            charm.on[relation_name].relation_departed,
            self._on_relation_departed,
        )

    def _on_relation_created(self, event: RelationCreatedEvent) -> None:
        """Handle the relation-created event."""
        if not self.model.unit.is_leader():
            return

        requirer_data = OpenfgaRequirerAppData(store_name=self.store_name)
        _update_relation_app_databag(self.app, event.relation, requirer_data.model_dump())

    def _on_relation_changed(self, event: RelationChangedEvent) -> None:
        """Handle the relation-changed event."""
        if not (app := event.relation.app):
            return

        databag = event.relation.data[app]
        try:
            data = OpenfgaProviderAppData.model_validate(databag)
        except pydantic.ValidationError:
            return

        self.on.openfga_store_created.emit(store_id=data.store_id)

    def _on_relation_departed(self, event: RelationDepartedEvent) -> None:
        """Handle the relation-departed event."""
        self.on.openfga_store_removed.emit()

    def _get_relation(self, relation_id: Optional[int] = None) -> Optional[Relation]:
        try:
            relation = self.model.get_relation(self.relation_name, relation_id=relation_id)
        except TooManyRelatedAppsError:
            raise RuntimeError("More than one relations are defined. Please provide a relation_id")
        if not relation or not relation.app:
            return None
        return relation

    def get_store_info(self) -> Optional[OpenfgaProviderAppData]:
        """Get the OpenFGA store and server info."""
        if not (relation := self._get_relation()):
            return None

        if not relation.app:
            return None

        databag = relation.data[relation.app]
        try:
            data = OpenfgaProviderAppData.model_validate(databag)
        except pydantic.ValidationError:
            return None

        if data.token_secret_id:
            token_secret = self.model.get_secret(id=data.token_secret_id)
            token = token_secret.get_content().get("token")
            data.token = token

        return data


class OpenFGAStoreRequestEvent(RelationEvent):
    """Event emitted when a new OpenFGA store is requested."""

    def __init__(self, handle: Handle, relation: Relation, store_name: str) -> None:
        super().__init__(handle, relation)
        self.store_name = store_name

    def snapshot(self) -> dict:
        """Save event."""
        dct = super().snapshot()
        dct["store_name"] = self.store_name
        return dct

    def restore(self, snapshot: dict) -> None:
        """Restore event."""
        super().restore(snapshot)
        self.store_name = snapshot["store_name"]


class OpenFGAProviderEvents(CharmEvents):
    """Custom charm events."""

    openfga_store_requested = EventSource(OpenFGAStoreRequestEvent)


class OpenFGAProvider(Object):
    """Requirer side of the openfga relation."""

    on = OpenFGAProviderEvents()

    def __init__(
        self,
        charm: CharmBase,
        relation_name: str = DEFAULT_INTEGRATION_NAME,
        http_port: Optional[str] = "8080",
        grpc_port: Optional[str] = "8081",
        scheme: Optional[str] = "http",
    ):
        super().__init__(charm, relation_name)
        self.charm = charm
        self.app = charm.app
        self.relation_name = relation_name
        self.http_port = http_port
        self.grpc_port = grpc_port
        self.scheme = scheme

        self.framework.observe(
            charm.on[relation_name].relation_changed,
            self._on_relation_changed,
        )

    def _on_relation_changed(self, event: RelationChangedEvent) -> None:
        if not (app := event.app):
            return

        if not (data := event.relation.data[app]):
            return

        try:
            data = OpenfgaRequirerAppData.model_validate(data)
        except pydantic.ValidationError:
            return

        self.on.openfga_store_requested.emit(event.relation, store_name=data.store_name)

    def update_relation_app_data(self, data: OpenfgaProviderAppData, relation_id: int) -> None:
        if not self.model.unit.is_leader():
            return

        relation = self.model.get_relation(self.relation_name, relation_id)
        if not relation or not relation.app:
            return

        if data.token_secret_id:
            try:
                secret = self.model.get_secret(id=data.token_secret_id)
            except Exception as e:
                logger.error("Failed to get secret %s: %s", data.token_secret_id, e)
                return

            secret.grant(relation)

        _update_relation_app_databag(
            self.app,
            relation,
            data.model_dump(),
        )

    def update_relations_app_data(self, data: OpenfgaProviderBaseData) -> None:
        if not self.model.unit.is_leader():
            return

        if not (relations := self.charm.model.relations.get(self.relation_name)):
            return

        for relation in relations:
            relation_data = relation.data[self.app]
            provider_data = OpenfgaProviderAppData(
                store_id=relation_data.get("store_id"),
                token_secret_id=relation_data.get("token_secret_id"),
                grpc_api_url=data.grpc_api_url,
                http_api_url=data.http_api_url,
            )

            _update_relation_app_databag(
                self.app,
                relation,
                provider_data.model_dump(),
            )
