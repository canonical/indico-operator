# How to configure the external hostname

To expose the application, deploy and integrate with the [Nginx Ingress Integrator Operator](https://charmhub.io/nginx-ingress-integrator). The charm will be automatically exposed at `[application name].local`, being `[application name]` the charm name. To provide a different hostname, set the [service-hostname](https://charmhub.io/nginx-ingress-integrator/configuration#service-hostname) configuration for the Nginx Ingress Integrator Operator.

Assuming Indico is already up and running as `indico`, you'll need to run the following commands:
```
# Deploy and integrate with the Nginx Ingress Integrator charm
juju deploy nginx-ingress-integrator
juju trust nginx-ingress-integrator --scope cluster # if RBAC is enabled
juju integrate nginx-ingress-integrator indico
# Configure the external hostname
juju config nginx-ingress-integrator service-hostname=indico.example
```
