# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.

"""Patch the ``ops-lib-pgsql`` library for unit testing.

This script is used to monkey patch necessary code to allow running unit tests with
``ops-lib-pgsql``. This patch needs to be run prior to the importing of the main module since
the main module uses ``ops.lib.use`` which runs ``exec_module`` internally and the
``ops-lib-pgsql`` just happens to use ``from .client import *``. Combined, that makes patching
any private variables inside ``pgsql.client`` afterwards impossible.
"""

from unittest.mock import MagicMock, patch

import ops.lib
import pgsql.client

__all__ = ["IndicoOperatorCharm", "pgsql_patch"]

_og_use = ops.lib.use


def _use(*args, **kwargs):
    print("use: ", args)
    if args == ("pgsql", 1, "postgresql-charmers@lists.launchpad.net"):
        return pgsql
    return _og_use(*args, **kwargs)


ops.lib.use = _use


class _PGSQLPatch:
    """The simulation of a Indico installed PGSQL database charm."""

    def __init__(self):
        """Initialize the instance."""
        # borrow some code from
        # https://github.com/canonical/ops-lib-pgsql/blob/master/tests/test_client.py
        self._leadership_data = {}
        self._patch = patch.multiple(
            pgsql.client,
            _is_ready=MagicMock(return_value=True),
            _get_pgsql_leader_data=self._leadership_data.copy,
            _set_pgsql_leader_data=self._leadership_data.update,
        )

    def _reset_leadership_data(self):
        """Clear the leadership data of the patched charm."""
        self._leadership_data.clear()

    def start(self):
        """Start the patched charm."""
        self._reset_leadership_data()
        self._patch.start()

    def stop(self):
        """Stop the patched charm."""
        self._reset_leadership_data()
        self._patch.stop()


pgsql_patch = _PGSQLPatch()
IndicoOperatorCharm = __import__("charm").IndicoOperatorCharm
EMAIL_LIST_MAX = __import__("charm").EMAIL_LIST_MAX
EMAIL_LIST_SEPARATOR = __import__("charm").EMAIL_LIST_SEPARATOR
