# How to configure SAML

To configure Indico's SAML integration you'll have to deploy the [SAML Integrator charm](https://charmhub.io/saml-integrator/docs/tutorial-getting-started) and integrate it with Indico by running `juju integrate indico saml-integrator`.

> **NOTE** At the moment, this feature has only been tested against Ubuntu SSO's SAML implementation. If you are having any issues configuring another SAML provider, please, reach out to us.