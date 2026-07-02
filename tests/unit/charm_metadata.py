# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

# Learn more about testing at: https://ops.readthedocs.io/en/latest/explanation/testing.html

"""Shared charm metadata for unit tests.

The flask-framework charmcraft extension injects containers, peers, relations,
actions and config options at pack time. ``ops.testing`` (Scenario) cannot
expand charmcraft extensions, so the fully-expanded metadata is materialised
here (from ``charmcraft expand-extensions``) for use by the unit tests.
"""

CHARM_META = {
    "name": "indico",
    "containers": {"flask-app": {"resource": "flask-app-image"}},
    "peers": {"secret-storage": {"interface": "secret-storage"}},
    "provides": {
        "metrics-endpoint": {"interface": "prometheus_scrape"},
        "grafana-dashboard": {"interface": "grafana_dashboard"},
    },
    "requires": {
        "postgresql": {"interface": "postgresql_client", "optional": False, "limit": 1},
        "redis": {"interface": "redis", "optional": False, "limit": 1},
        "s3": {"interface": "s3", "optional": True, "limit": 1},
        "smtp": {"interface": "smtp", "optional": True, "limit": 1},
        "saml": {"interface": "saml", "optional": True, "limit": 1},
        "oauth": {"interface": "oauth", "optional": True, "limit": 1},
        "logging": {"interface": "loki_push_api"},
        "ingress": {"interface": "ingress", "limit": 1},
    },
    "resources": {
        "flask-app-image": {"type": "oci-image", "description": "flask application image."}
    },
}

CHARM_ACTIONS = {
    "add-admin": {
        "description": "Add an admin to Indico.",
        "params": {
            "email": {"type": "string", "description": "User email."},
            "password": {"type": "string", "description": "User password."},
        },
        "required": ["email", "password"],
    },
    "anonymize-user": {
        "description": "Anonymize stored personal data to facilitate GDPR compliance.",
        "params": {
            "email": {
                "type": "string",
                "description": "User email (or a "
                "list of emails "
                "separated by "
                "comma). Maximum "
                "of 50 emails.",
            }
        },
        "required": ["email"],
    },
    "refresh-external-resources": {
        "description": "Reinstall/upgrade the external plugins listed in `external_plugins`."
    },
    "rotate-secret-key": {
        "description": "Rotate the secret key. Users will be "
        "forced to log in again. This might be "
        "useful if a security breach occurs."
    },
}

CHARM_CONFIG = {
    "options": {
        "site_url": {
            "type": "string",
            "default": "",
            "description": "URL through which Indico is "
            "accessed by users. Parsed for "
            "scheme,\n"
            "hostname and optional port; "
            "surfaced to the workload as\n"
            "FLASK_SITE_URL and turned into "
            "`BASE_URL` in indico.conf. Empty\n"
            "value defaults to "
            "`http://<app-name>.local`.\n",
        },
        "external_plugins": {
            "type": "string",
            "default": "",
            "description": "Comma separated list of "
            "external plugins to be "
            "installed, e.g.\n"
            "git+https://github.com/indico/indico-plugins-cern.git/#subdirectory=themes_cern.\n"
            "The format of each item "
            "must be supported by pip. "
            "Installed at\n"
            "workload startup on top of "
            "the default plugins baked "
            "into the rock.\n",
        },
        "indico_no_reply_email": {
            "type": "string",
            "default": "noreply@mydomain.local",
            "description": "Email address used "
            "when sending emails to "
            "users to which they\n"
            "should not reply.\n",
        },
        "indico_public_support_email": {
            "type": "string",
            "default": "support@mydomain.local",
            "description": 'Email address that is shown to users on the "Contact" page.',
        },
        "indico_support_email": {
            "type": "string",
            "default": "support-tech@mydomain.local",
            "description": "Email address of the technical manager of the Indico instance.",
        },
        "secret-key": {
            "type": "secret",
            "description": "Juju user secret containing the "
            "Flask `SECRET_KEY`. Expected as "
            "a\n"
            "hex-encoded byte string; the "
            "workload falls back to treating "
            "the\n"
            "value as a plain UTF-8 string if "
            "hex decoding fails.\n",
        },
        "enabled-plugins": {
            "type": "string",
            "default": "",
            "description": "Space-separated list of "
            "Indico plugin names to "
            "enable at runtime\n"
            "(for example, "
            "`payment_paypal piwik "
            "storage_s3`). The "
            "corresponding\n"
            "plugin packages must already "
            "be installed in the rock or "
            "via the\n"
            "`external_plugins` option "
            "above.\n",
        },
        "pip-index-url": {
            "type": "string",
            "default": "",
            "description": "Optional PyPI index URL used "
            "when installing "
            "`external_plugins`. Set\n"
            "this for air-gapped "
            "environments that mirror PyPI "
            "on an internal\n"
            "registry. Empty value means "
            "the public PyPI index is "
            "used.\n",
        },
        "local-identities": {
            "type": "boolean",
            "default": True,
            "description": "Whether the built-in local "
            "username/password login "
            "stays enabled. Keep\n"
            "`true` so the bootstrap "
            "admin can log in alongside "
            "SSO providers; set\n"
            "`false` to force "
            "authentication exclusively "
            "through SSO.\n",
        },
        "webserver-keepalive": {
            "type": "int",
            "description": "Time in seconds for "
            "webserver to wait for "
            "requests on a Keep-Alive "
            "connection.",
        },
        "webserver-threads": {
            "type": "int",
            "description": "Run each webserver worker with the specified number of threads.",
        },
        "webserver-timeout": {
            "type": "int",
            "description": "Time in seconds to kill and restart silent webserver workers.",
        },
        "webserver-workers": {
            "type": "int",
            "description": "The number of webserver worker processes for handling requests.",
        },
        "webserver-worker-class": {
            "type": "string",
            "description": "The webserver worker "
            "process class for "
            "handling requests. "
            "Can be either "
            "'gevent' or 'sync'.",
        },
        "flask-application-root": {
            "type": "string",
            "description": "Path in which the "
            "application / web "
            "server is mounted. "
            "This configuration "
            "will set the "
            "FLASK_APPLICATION_ROOT "
            "environment variable. "
            "Run "
            "`app.config.from_prefixed_env()` "
            "in your Flask "
            "application in order "
            "to receive this "
            "configuration.",
        },
        "flask-debug": {"type": "boolean", "description": "Whether Flask debug mode is enabled."},
        "flask-env": {
            "type": "string",
            "description": "What environment the Flask app is "
            "running in, by default it's "
            "'production'.",
        },
        "flask-permanent-session-lifetime": {
            "type": "int",
            "description": "Time in "
            "seconds for "
            "the cookie "
            "to expire "
            "in the "
            "Flask "
            "application "
            "permanent "
            "sessions. "
            "This "
            "configuration "
            "will set "
            "the "
            "FLASK_PERMANENT_SESSION_LIFETIME "
            "environment "
            "variable. "
            "Run "
            "`app.config.from_prefixed_env()` "
            "in your "
            "Flask "
            "application "
            "in order to "
            "receive "
            "this "
            "configuration.",
        },
        "flask-preferred-url-scheme": {
            "type": "string",
            "default": "HTTPS",
            "description": "Scheme for "
            "generating "
            "external URLs "
            "when not in a "
            "request context "
            "in the Flask "
            "application. By "
            "default, it's "
            '"HTTPS". This '
            "configuration "
            "will set the "
            "FLASK_PREFERRED_URL_SCHEME "
            "environment "
            "variable. Run "
            "`app.config.from_prefixed_env()` "
            "in your Flask "
            "application in "
            "order to receive "
            "this "
            "configuration.",
        },
        "flask-secret-key": {
            "type": "string",
            "description": "The secret key used for "
            "securely signing the "
            "session cookie and for any "
            "other security related "
            "needs by your Flask "
            "application. This "
            "configuration will set the "
            "FLASK_SECRET_KEY "
            "environment variable. Run "
            "`app.config.from_prefixed_env()` "
            "in your Flask application "
            "in order to receive this "
            "configuration.",
        },
        "flask-secret-key-id": {
            "type": "secret",
            "description": "This configuration is "
            "similar to "
            "`flask-secret-key`, but "
            "instead accepts a Juju "
            "user secret ID. The "
            "secret should contain a "
            'single key, "value", '
            "which maps to the actual "
            "Flask secret key. To "
            "create the secret, run "
            "the following command: "
            "`juju add-secret "
            "my-flask-secret-key "
            "value=<secret-string> && "
            "juju grant-secret "
            "my-flask-secret-key "
            "flask-k8s`, and use the "
            "output secret ID to "
            "configure this option.",
        },
        "flask-session-cookie-secure": {
            "type": "boolean",
            "description": "Set the secure "
            "attribute in the "
            "Flask "
            "application "
            "cookies. This "
            "configuration "
            "will set the "
            "FLASK_SESSION_COOKIE_SECURE "
            "environment "
            "variable. Run "
            "`app.config.from_prefixed_env()` "
            "in your Flask "
            "application in "
            "order to receive "
            "this "
            "configuration.",
        },
        "oauth-redirect-path": {
            "type": "string",
            "description": "The path that the user will be redirected upon completing login.",
            "default": "/callback",
        },
        "oauth-scopes": {
            "type": "string",
            "description": "A list of scopes with spaces in between.",
            "default": "openid profile email",
        },
    }
}
