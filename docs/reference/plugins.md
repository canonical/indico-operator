# Plugins

Indico provides many plugins that can be used to extend functionalities without the need to change the Indico core. See more information in [Extending Indico with plugins](https://docs.getindico.io/en/latest/plugins/).

You can configure additional plugins using the [`external_plugins`](https://charmhub.io/indico/configure#external_plugins) configuration option.

There is a special treatment for the [Flask-Multipass-SAML-Groups](https://github.com/canonical/flask-multipass-saml-groups/) plugin: 
When this plugin is configured, the charm will automatically configure Indico to use the provided custom Indico Identity Provider `saml_groups` if a saml integration is available is configured.
