"""Library for the redis relation.

This library contains the Requires and Provides classes for handling the
redis interface.

Import `RedisRequires` in your charm by adding the following to `src/charm.py`:
```
from charms.redis_k8s.v0.redis import RedisRequires
```
And then in your charm's `__init__` method:
```
# Make sure you set redis_relation in StoredState. Assuming you refer to this
# as `self._stored`:
self._stored.set_default(redis_relation={})
self.redis = RedisRequires(self, self._stored)
```
And then wherever you need to reference the relation data it will be available
via StoredState:
```
redis_hosts = []
for redis_unit in self._stored.redis_relation:
    redis_hosts.append({
        "redis-host": self._stored.redis_relation[redis_unit]["hostname"],
        "redis-port": self._stored.redis_relation[redis_unit]["port"],
    })
```
You will also need to add the following to `metadata.yaml`:
```
requires:
  redis:
    interface: redis
```
"""
import logging
import socket
from typing import Dict, Optional

from ops.charm import CharmEvents
from ops.framework import EventBase, EventSource, Object

# The unique Charmhub library identifier, never change it.
LIBID = "fe18a608cec5465fa5153e419abcad7b"

# Increment this major API version when introducing breaking changes.
LIBAPI = 0

# Increment this PATCH version before using `charmcraft publish-lib` or reset
# to 0 if you are raising the major API version.
LIBPATCH = 4

logger = logging.getLogger(__name__)

DEFAULT_REALTION_NAME = "redis"

class RedisRelationUpdatedEvent(EventBase):
    """An event for the redis relation having been updated."""


class RedisRelationCharmEvents(CharmEvents):
    """A class to carry custom charm events so requires can react to relation changes."""
    redis_relation_updated = EventSource(RedisRelationUpdatedEvent)


class RedisRequires(Object):

    def __init__(self, charm, _stored, relation_name: str = DEFAULT_REALTION_NAME):
        """A class implementing the redis requires relation."""
        super().__init__(charm, relation_name)
        self.framework.observe(charm.on[relation_name].relation_joined, self._on_relation_changed)
        self.framework.observe(charm.on[relation_name].relation_changed, self._on_relation_changed)
        self.framework.observe(charm.on[relation_name].relation_broken, self._on_relation_broken)
        self._stored = _stored
        self.charm = charm
        self.relation_name = relation_name

    def _on_relation_changed(self, event):
        """Handle the relation changed event."""
        if not event.unit:
            return

        hostname = event.relation.data[event.unit].get("hostname")
        port = event.relation.data[event.unit].get("port")
        self._stored.redis_relation[event.relation.id] = {"hostname": hostname, "port": port}

        # Trigger an event that our charm can react to.
        self.charm.on.redis_relation_updated.emit()

    def _on_relation_broken(self, event):
        """Handle the relation broken event."""
        # Remove the unit data from local state.
        self._stored.redis_relation.pop(event.relation.id, None)

        # Trigger an event that our charm can react to.
        self.charm.on.redis_relation_updated.emit()

    def get_relation_data(self) -> Optional[Dict[str, str]]:
        """Retrieve the relation data.

        Returns:
            Dict: dict containing the relation data.
        """
        relation = self.model.get_relation(self.relation_name)
        if not relation or not relation.units:
            return None
        unit = next(iter(relation.units))
        return relation.data[unit]

    def get_url(self) -> Optional[str]:
        """Retrieve the Redis URL.

        Returns:
            str: the Redis URL.
        """
        relation_data = self.get_relation_data()
        if not relation_data:
            return None
        redis_host = relation_data.get("hostname")
        redis_port = relation_data.get("port")
        return f"redis://{redis_host}:{redis_port}"


class RedisProvides(Object):
    def __init__(self, charm, port):
        """A class implementing the redis provides relation."""
        super().__init__(charm, DEFAULT_REALTION_NAME)
        self.framework.observe(charm.on.redis_relation_changed, self._on_relation_changed)
        self._port = port
        self._charm = charm

    def _on_relation_changed(self, event):
        """Handle the relation changed event."""
        event.relation.data[self.model.unit]["hostname"] = self._get_master_ip()
        event.relation.data[self.model.unit]["port"] = str(self._port)
        # The reactive Redis charm also exposes 'password'. When tackling
        # https://github.com/canonical/redis-k8s/issues/7 add 'password'
        # field so that it matches the exposed interface information from it.
        # event.relation.data[self.unit]['password'] = ''

    def _bind_address(self, event):
        """Convenience function for getting the unit address."""
        relation = self.model.get_relation(event.relation.name, event.relation.id)
        if address := self.model.get_binding(relation).network.bind_address:
            return address
        return self.app.name

    def _get_master_ip(self) -> str:
        """Gets the ip of the current redis master."""
        return socket.gethostbyname(self._charm.current_master)
