# Indico Operator

## Description

A Juju charm deploying and managing Indico on Kubernetes, configurable to use a PostgreSQL and Redis backend.


## Usage

To deploy into a Juju K8s model:

    juju deploy postgresql-k8s
    juju deploy redis-k8s redis-broker
    juju deploy redis-k8s redis-cache
    juju deploy indico
    juju relate indico postgresql-k8s:db
    juju relate redis-broker indico
    juju relate redis-cache indico


The charm supports the `ingress` relation, which can be used with
[nginx-ingress-integrator](https://charmhub.io/nginx-ingress-integrator/).

    juju deploy nginx-ingress-integrator
    juju relate indico:ingress nginx-ingress-integrator:ingress


For further details, [see here](https://charmhub.io/indico/docs).

## Development

This project uses [tox](https://tox.wiki/en/latest/). These commands have been
defined:

* formatting the code: `tox -e fmt`
* linting the code: `tox -e lint`
* running unit tests: `tox -e unit`
* running integration tests: `tox -e integration`

To deploy for development, use the same commands as above except for
`juju deploy indico`, use the following instead:

    # Build the indico docker images
    docker build . -f indico.Dockerfile -t localhost:32000/indico:latest
    docker push localhost:32000/indico:latest
    docker build . -f indico-nginx.Dockerfile -t  localhost:32000/indico-nginx:latest
    docker push localhost:32000/indico-nginx:latest
    # Build the charm
    charmcraft pack
    # Deploy the charm
    juju deploy ./indico_ubuntu-20.04-amd64.charm --resource indico-image=localhost:32000/indico:latest --resource indico-nginx-image=localhost:32000/indico-nginx:latest

Assuming that microk8s is used for juju and that the local registry is
enabled: `microk8s enable registry`
