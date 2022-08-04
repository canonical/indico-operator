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

Assuming
[juju and microk8s have been setup](https://juju.is/docs/olm/microk8s).

This project uses [tox](https://tox.wiki/en/latest/). These commands have been
defined:

* formatting the code: `tox -e fmt`
* linting the code: `tox -e lint`
* running unit tests: `tox -e unit`
* running integration tests: `tox -e integration  -- --indico-image localhost:32000/indico:latest --indico-nginx-image=localhost:32000/indico-nginx:latest`

For the integration tests (and also to deploy the charm locally), the indico
and indico-nginx images are required in the microk8s registry. To enable it:

    microk8s enable registry

The following commands push the required images into the registry:

    docker build . -f indico.Dockerfile -t localhost:32000/indico:latest
    docker push localhost:32000/indico:latest
    docker build . -f indico-nginx.Dockerfile -t  localhost:32000/indico-nginx:latest
    docker push localhost:32000/indico-nginx:latest

To deploy for development, use the same commands as above except for
`juju deploy indico`, use the following instead:

    # Build the charm
    charmcraft pack
    # Deploy the charm
    juju deploy ./indico_ubuntu-20.04-amd64.charm --resource indico-image=localhost:32000/indico:latest --resource indico-nginx-image=localhost:32000/indico-nginx:latest
