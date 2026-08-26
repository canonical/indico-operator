#!/usr/bin/env python3
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""Connect our CLI plugin to the existing Indico's CLI."""

from indico.core import signals
from indico.core.plugins import IndicoPlugin

from autocreate.cli import cli


class AutocreatePlugin(IndicoPlugin):
    """Autocreate.

    Provides a way to non-interactively create users via Indico's CLI
    """

    def init(self):
        """Construct."""
        super().init()
        self.connect(signals.plugin.cli, self._extend_indico_cli)

    def _extend_indico_cli(self, *_, **__):
        """Return the indico extended cli.

        Returns:
            Indico's CLI with extra parameters.
        """
        return cli
