# Indico Operator

A Juju charm deploying and managing Indico on Kubernetes. Indico is an
open-source tool for event organisation, archival and collaboration.

This charm simplifies initial deployment and "day N" operations of Indico
on Kubernetes, such as scaling the number of instances, integration with SSO,
access to S3 for redundant file storage and more. It allows for deployment on
many different Kubernetes platforms, from [MicroK8s](https://microk8s.io) to
[Charmed Kubernetes](https://ubuntu.com/kubernetes) to public cloud Kubernetes
offerings.

As such, the charm makes it easy for those looking to take control of their own
events management system whilst keeping operations simple, and gives them the
freedom to deploy on the Kubernetes platform of their choice.

For DevOps or SRE teams this charm will make operating Indico simple and
straightforward through Juju's clean interface. It will allow easy deployment
into multiple environments for testing of changes, and supports scaling out for
enterprise deployments.

## Deployment options overview

For overall concepts related to using Juju
[see the Juju overview page](https://juju.is/). For easy local testing we
recommend
[this how to on using MicroK8s with Juju](https://juju.is/docs/microk8s-cloud).

## How to deploy this charm (quick guide)

To deploy the charm and relate it to
[the PostgreSQL K8s charm](https://charmhub.io/postgresql-k8s) and
[the Redis K8s charm](https://charmhub.io/redis-k8s) within a Juju Kubernetes model:

    juju deploy postgresql-k8s
    juju deploy redis-k8s redis-broker
    juju deploy redis-k8s redis-cache
    juju deploy indico
    juju relate indico postgresql-k8s:db
    juju relate redis-broker indico
    juju relate redis-cache indico
    
The charm also supports the `ingress` relation, which can be used with
[nginx-ingress-integrator](https://charmhub.io/nginx-ingress-integrator/).

    juju deploy nginx-ingress-integrator
    juju relate indico:ingress nginx-ingress-integrator:ingress

Once the deployment has completed and the "indico" workload state in
`juju status` has changed to "active" you can visit `http://indico.local` in
a browser (assuming `indico` resolves to the IP(s) of your k8s ingress)
and log in to your Indico instance, and you'll be presented with a screen
to create an initial admin account. Further accounts must be created using this
admin account, or by setting up an external authentication source, such as
SAML.

For further details,
[see the charm's detailed documentation](https://charmhub.io/indico/docs).
