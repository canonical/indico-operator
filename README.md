[![CharmHub Badge](https://charmhub.io/indico/badge.svg)](https://charmhub.io/indico)
[![Publish to edge](https://github.com/canonical/indico-operator/actions/workflows/publish_charm.yaml/badge.svg)](https://github.com/canonical/indico-operator/actions/workflows/publish_charm.yaml)
[![Promote charm](https://github.com/canonical/indico-operator/actions/workflows/promote_charm.yaml/badge.svg)](https://github.com/canonical/indico-operator/actions/workflows/promote_charm.yaml)
[![Discourse Status](https://img.shields.io/discourse/status?server=https%3A%2F%2Fdiscourse.charmhub.io&style=flat&label=CharmHub%20Discourse)](https://discourse.charmhub.io)

# Indico Operator

A Juju charm deploying and managing Indico on Kubernetes. Indico is an
open-source tool for event organisation, archival and collaboration. It allows for deployment on
many different Kubernetes platforms, from [MicroK8s](https://microk8s.io) to
[Charmed Kubernetes](https://ubuntu.com/kubernetes) to public cloud Kubernetes
offerings.

Like any Juju charm, this charm supports one-line deployment, configuration, integration, scaling, and more. For Charmed Indico, this includes:
  - Scaling
  - Integration with SSO
  - Integration with S3 for redundant file storage

For information about how to deploy, integrate, and manage this charm, see the Official [Indico Operator Documentation](https://charmhub.io/indico/docs).


## Get started

You can follow the tutorial [here](https://charmhub.io/indico/docs/tutorial).

### Basic operations

The following actions are available for this charm:
  - refresh-external-resources: refresh the external resources (e.g. S3 bucket)
  - add-admmin: add an admin user
  - anonymize-user: anonymize a user

You can check out the [full list of actions here](https://charmhub.io/indico/actions).

## Integrations

This charm can be integrated with other Juju charms and services:

  - [Redis](https://charmhub.io/redis-k8s): Redis is an open source (BSD licensed), in-memory data structure store, used as a database, cache and message broker.
  - [S3](https://charmhub.io/s3-integrator): Amazon Simple Storage Service (Amazon S3) is an object storage service that provides secure, durable, highly available storage with massive scalability and low latency.
  - [Postgresql](https://charmhub.io/postgresql-k8s): PostgreSQL is a powerful, open source object-relational database system. It has more than 15 years of active development and a proven architecture that has earned it a strong reputation for reliability, data integrity, and correctness.

  and much more. You can find the full list of integrations [here](https://charmhub.io/indico/integrations).

## Learn more
* [Read more](https://charmhub.io/indico) <!--Link to the charm's official documentation-->
* [Developer documentation](https://docs.getindico.io/en/stable/) <!--Link to any developer documentation-->
* [Official webpage](https://indico.cern.ch/) <!--(Optional) Link to official webpage/blog/marketing content-->
* [Troubleshooting](https://matrix.to/#/#charmhub-charmdev:ubuntu.com) <!--(Optional) Link to a page or section about troubleshooting/FAQ-->
## Project and community
* [Issues](https://github.com/canonical/indico-operator/issues) <!--Link to GitHub issues (if applicable)-->
* [Contributing](https://charmhub.io/indico/docs/how-to-contribute) <!--Link to any contribution guides-->
* [Matrix](https://matrix.to/#/#charmhub-charmdev:ubuntu.com) <!--Link to contact info (if applicable), e.g. Matrix channel-->
