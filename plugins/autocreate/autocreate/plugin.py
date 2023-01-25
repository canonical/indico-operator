from indico.core import signals
from indico.core.plugins import IndicoPlugin

from autocreate.cli import cli
from autocreate import _


class AutocreatePlugin(IndicoPlugin):
    """Autocreate

    Provides a way to non-interactively create users via Indico's CLI
    """

    def init(self):
        super().init()
        self.connect(signals.plugin.cli, self._extend_indico_cli)

    def _extend_indico_cli(self, sender, **kwargs):
        return cli
