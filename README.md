# indico-operator

## Description

A Juju charm deploying and managing Indico on Kubernetes, configurable to use a PostgreSQL and Redis backend.


## Usage

To deploy into a Juju K8s model:

    juju deploy postgresql-k8s
    juju deploy redis-k8s
    juju deploy indico-k8s
    juju relate indico-k8s redis-k8s
    juju relate indico-k8s postgresql-k8s:db

The charm supports the `ingress` relation, which can be used with
[nginx-ingress-integrator](https://charmhub.io/nginx-ingress-integrator/)

    juju deploy nginx-ingress-integrator
    juju relate indico-k8s:ingress nginx-ingress-integrator:ingress


## Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines
on enhancements to this charm following best practice guidelines, and
`CONTRIBUTING.md` for developer guidance.
