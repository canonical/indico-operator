# How to configure the external hostname

This charm exposes the `site_url` configuration option to specify the external hostname of the application.

To expose the application it is recommended to set that configuration option and deploy and integrate with the [Nginx Ingress Integrator Operator](https://charmhub.io/nginx-ingress-integrator), that will be automatically configured with the values provided by the charm.

Assuming Indico is already up and running as `indico`, you'll need to run the following commands:
```
# Configure the external hostname
juju config indico site_url=indico.local
# Deploy and integrate with the Nginx Ingress Integrator charm
juju deploy nginx-ingress-integrator
juju trust nginx-ingress-integrator --scope cluster # if RBAC is enabled
juju integrate nginx-ingress-integrator indico
```

For more details on the configuration options and their default values see the [configuration reference](https://charmhub.io/indico/configure).