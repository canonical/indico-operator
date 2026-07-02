# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

"""WSGI entrypoint shim for the flask-framework Rockcraft extension.

The extension's default Gunicorn command resolves ``app:app``. Indico itself
exposes an application factory at ``indico.web.flask.app:make_app``; this shim
adapts the two so the extension contract is satisfied without overriding the
Pebble service command.
"""

from indico.web.flask.app import make_app

app = make_app()
