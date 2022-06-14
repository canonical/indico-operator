# Indico Operator

## Description

A Juju charm deploying and managing Indico on Kubernetes, configurable to use a PostgreSQL and Redis backend.


## Usage

To deploy into a Juju K8s model:

    juju deploy postgresql-k8s
    juju deploy redis-k8s
    juju deploy indico
    juju relate indico redis-k8s
    juju relate indico postgresql-k8s:db

The charm supports the `ingress` relation, which can be used with
[nginx-ingress-integrator](https://charmhub.io/nginx-ingress-integrator/).

    juju deploy nginx-ingress-integrator
    juju relate indico:ingress nginx-ingress-integrator:ingress


For further details, [see here](https://charmhub.io/indico/docs).
