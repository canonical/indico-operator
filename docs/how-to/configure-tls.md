# How to configure a TLS certificate

First you'll need a k8s secret with key and cert values as appropiate.

Then, use that secret to configure your nginx-ingress-integrator. You do this by running:
```
juju config nginx-ingress-integrator tls-secret-name="my-tls-secret"
```

Please see the [securing an ingress documentation](https://charmhub.io/nginx-ingress-integrator/docs/secure-an-ingress-with-tls) page for more information.
