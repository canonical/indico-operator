# How to configure a TLS certificate

You do this by running
```
juju config nginx-ingress-integrator tls-secret-name="my-tls-secret"
```
Being "my-tls-secret" an already existing k8s secret.

Please see the [securing an ingress documentation](https://charmhub.io/nginx-ingress-integrator/docs/secure-an-ingress-with-tls) page for more information.
