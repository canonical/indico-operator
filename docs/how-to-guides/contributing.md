# Contributing

## Overview

This document explains the processes and practices recommended for contributing enhancements to the Indico operator.

- Generally, before developing enhancements to this charm, you should consider [opening an issue
  ](https://github.com/canonical/indico-operator/issues) explaining your use case.
- If you would like to chat with us about your use-cases or proposed implementation, you can reach
  us at [Canonical Mattermost public channel](https://chat.charmhub.io/charmhub/channels/charm-dev)
  or [Discourse](https://discourse.charmhub.io/).
- Familiarising yourself with the [Charmed Operator Framework](https://juju.is/docs/sdk) library
  will help you a lot when working on new features or bug fixes.
- All enhancements require review before being merged. Code review typically examines
  - code quality
  - test coverage
  - user experience for Juju administrators of this charm.
- Please help us out in ensuring easy to review branches by rebasing your pull request branch onto the `main` branch. This also avoids merge commits and creates a linear Git commit history.

## Developing

The code for this charm can be downloaded as follows:

```
git clone https://github.com/canonical/indico-operator
```

You can use the environments created by `tox` for development:

```shell
tox --notest -e unit
source .tox/unit/bin/activate
```

### Testing

```shell
tox -e fmt           # update your code according to linting rules
tox -e lint          # code style
tox -e unit          # unit tests
# integration tests (see below for building docker images)
tox -e integration -- --indico-image localhost:32000/indico:latest --indico-nginx-image=localhost:32000/indico-nginx:latest
tox                  # runs 'lint' and 'unit' environments
```

## Build charm

Build the charm in this git repository using:

```shell
charmcraft pack
```
For the integration tests (and also to deploy the charm locally), the indico
and indico-nginx images are required in the microk8s registry. To enable it:

    microk8s enable registry

The following commands push the required images into the registry:

    docker build . -f indico.Dockerfile -t localhost:32000/indico:latest
    docker push localhost:32000/indico:latest
    docker build . -f indico-nginx.Dockerfile -t  localhost:32000/indico-nginx:latest
    docker push localhost:32000/indico-nginx:latest

### Deploy

```bash
# Create a model
juju add-model indico-dev
# Enable DEBUG logging
juju model-config logging-config="<root>=INFO;unit=DEBUG"
# Deploy the charm (Assuming you're on amd64)
juju deploy ./indico_ubuntu-20.04-amd64.charm \
  --resource indico-image=localhost:32000/indico:latest \
  --resource indico-nginx-image=localhost:32000/indico-nginx:latest \
  --resource nginx-prometheus-exporter-image='nginx/nginx-prometheus-exporter:0.10.0' \
  --resource statsd-prometheus-exporter-image='prom/statsd-exporter:v0.22.8'
```

## Canonical Contributor Agreement

Canonical welcomes contributions to the Indico Operator. Please check out our [contributor agreement](https://ubuntu.com/legal/contributors) if you're interested in contributing to the solution.
