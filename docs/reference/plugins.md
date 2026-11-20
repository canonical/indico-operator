# Plugins

Indico provides many plugins that can be used to extend functionalities without the need to change the Indico core. See more information in [Extending Indico with plugins](https://docs.getindico.io/en/latest/plugins/).

## Plugins shipped with the charm

The following plugins are packed as part of the Indico rock used by the charm and are available without any additional configuration.

| Plugin | Package | Description |
|--------|---------|-------------|
| `payment_paypal` | [`indico-plugin-payment-paypal`](https://pypi.org/project/indico-plugin-payment-paypal/) | Official Indico plugin that provides PayPal as a payment method for event registrations. |
| `piwik` | [`indico-plugin-piwik`](https://pypi.org/project/indico-plugin-piwik/) | Official Indico plugin that tracks statistics of events and their materials with Matomo (formerly Piwik). |
| `storage_s3` | [`indico-plugin-storage-s3`](https://pypi.org/project/indico-plugin-storage-s3/) | Official Indico plugin that stores files in S3-compatible object storage. |
| `autocreate` | [`indico-plugin-autocreate`](https://github.com/canonical/indico-operator/tree/main/indico_rock/plugins/autocreate) | Extends the Indico CLI to add a non-interactive way to create users. Used by the [`add-admin`](https://charmhub.io/indico/actions#add-admin) action. |
| `anonymize` | [`indico-plugin-anonymize`](https://github.com/canonical/indico-operator/tree/main/indico_rock/plugins/anonymize) | Extends the Indico CLI to add a non-interactive way to anonymize users. Used by the [`anonymize-user`](https://charmhub.io/indico/actions#anonymize-user) action. |

> **NOTE** The plugins shipped with the charm are built into the rock, and their versions are fixed for each charm revision. These plugins can't be customized or updated through the charm configuration. Changes to these plugins require a contribution to the [indico-operator](https://github.com/canonical/indico-operator) repository and a new release of the charm.

## External plugins

You can configure additional plugins using the [`external_plugins`](https://charmhub.io/indico/configure#external_plugins) configuration option.

There is a special treatment for the [Flask-Multipass-SAML-Groups](https://github.com/canonical/flask-multipass-saml-groups/) plugin: 
When this plugin is installed, the charm will automatically configure Indico to use the provided custom Indico Identity Provider `saml_groups` if a saml integration is available.
