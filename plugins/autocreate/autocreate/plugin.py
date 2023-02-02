#!/usr/bin/env python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""Connect our CLI plugin to the existing Indico's CLI."""

from autocreate.cli import cli
from indico.core import signals
from indico.core.plugins import IndicoPlugin


class AutocreatePlugin(IndicoPlugin):
    """Autocreate

    Provides a way to non-interactively create users via Indico's CLI
    """

    def init(self):
        super().init()
        self.connect(signals.plugin.cli, self._extend_indico_cli)

    # We need thos arguments when extending indico's CLI
    # pylint: disable=unused-argument
    def _extend_indico_cli(self, *args, **kwargs):
        return cli
