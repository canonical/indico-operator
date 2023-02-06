# SAML configuration

To configure Indico's SAML integration you'll have to set `saml_target_url` with the URL for your SAML server by running `juju config [charm_name] saml_target_url=[value]`.

At the moment, this feature has only been tested against Ubuntu SSO's SAML implementation. If you are having any issues configuring another SAML provider, please, reach out to us.

For more details on the configuration options and their default values see the [configuration reference](https://charmhub.io/indico/configure).
