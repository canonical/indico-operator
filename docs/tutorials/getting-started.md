# Quick Guide

## What you’ll learn

- Deploy the [Indico charm](https://charmhub.io/indico).
- Relate to [the Redis K8s charm](https://charmhub.io/redis-k8s) and [the PostgreSQL K8s charm](https://charmhub.io/postgresql-k8s).
- Relate to [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/#what-is-ingress) by using [NGINX Ingress Integrator](https://charmhub.io/nginx-ingress-integrator/).

Through the process, you'll inspect the Kubernetes resources created, verify the workload state, and log in to your Indico instance.

## Requirements

- Juju 3 installed.
- Juju controller and model created.
- NGINX Ingress Controller. If you're using [MicroK8s](https://microk8s.io/), this can be done by running the command `microk8s enable ingress`. For more details, see [Addon: Ingress](https://microk8s.io/docs/addon-ingress).

For more information about how to install Juju, see [Get started with Juju](https://juju.is/docs/olm/get-started-with-juju).

### Deploy the Indico charm

Since Indico requires connections to PostgreSQL and Redis, you'll deploy them too. For more information, see [Charm Architecture](https://charmhub.io/indico/docs/charm-architecture).

Redis is deployed twice because one is for the broker and the other for the cache. To do this, the `juju deploy` command accepts an extra argument with the custom application name. See more details in [Override the name of a deployed application](https://juju.is/docs/olm/deploy-a-charm-from-charmhub#heading--override-the-name-of-a-deployed-application).

Deploy the charms:

```bash
juju deploy postgresql-k8s
juju deploy redis-k8s redis-broker
juju deploy redis-k8s redis-cache
juju deploy indico
```

To see the pod created by the Indico charm, run `kubectl get pods` on a namespace named for the Juju model you've deployed the Indico charm into. The output is similar to the following:

```bash
NAME                             READY   STATUS    RESTARTS   AGE
indico-0                         7/7     Running   0         6h4m
```

Run [`juju status`](https://juju.is/docs/olm/juju-status) to see the current status of the deployment. In the Unit list, you can see that Indico is waiting:

```bash
indico/0*                 waiting   idle   10.1.74.70             Waiting for redis-broker availability
```

This means that Indico charm isn't integrated with Redis yet.

### Relate to the Redis K8s charm the PostgreSQL K8s charm

Provide integration between Indico and Redis by running the following [`juju relate`](https://juju.is/docs/olm/juju-relate) commands:

```bash
juju relate redis-broker indico
juju relate redis-cache indico
```

Run `juju status` to see that the message has changed:

```bash
indico/0*                 waiting   idle   10.1.74.70             Waiting for database availability
```

Provide integration between Indico and PostgreSQL:

```bash
juju relate indico postgresql-k8s:db
```

Note: `db` is the name of the relation. This is needed because establishes that the two charms are compatible with each other.  You can run `juju info indico` to check what are the relation names required by the Indico application.

Run `juju status` and wait until the Application status is `Active` as the following example:

Optional: run `juju status --relations --watch 5s` to watch the status every 5 seconds with the Relations section.

```bash
App                       Version                       Status  Scale  Charm                     Channel  Rev  Address         Exposed  Message
indico                 3.2                           active      1  indico                              17  10.152.183.68   no
```

The deployment finishes when the status shows "Active".

### Relate to Ingress by using NGINX Ingress Integrator

The NGINX Ingress Integrator charm can deploy and manage external access to HTTP/HTTPS services in a Kubernetes cluster.

If you want to make Indico charm available to external clients, you need to deploy the NGINX Ingress Integrator charm and integrate Indico with it.

See more details in [Adding the Ingress Relation to a Charm](https://charmhub.io/nginx-ingress-integrator/docs/adding-ingress-relation).

Deploy the charm NGINX Ingress Integrator:

```bash
juju deploy nginx-ingress-integrator
```

If your cluster has [RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/) enabled, you'll be prompted to run the following:

```bash
juju trust nginx-ingress-integrator --scope cluster
```

Run `juju status` to verify the deployment.

Provide integration between Indico and NGINX Ingress Integrator:

```bash
juju relate indico nginx-ingress-integrator

```

To see the Ingress resource created, run `kubectl get ingress` on a namespace named for the Juju model you've deployed the Indico charm into. The output is similar to the following:

```bash
NAME                      CLASS    HOSTS             ADDRESS     PORTS   AGE
indico-local-ingress      public   indico.local   127.0.0.1   80      2d
```

Run `juju status` to see the same Ingress IP in the `nginx-ingress-integrator` message:

```bash
nginx-ingress-integrator                                active      1  nginx-ingress-integrator  stable    45  10.152.183.233  no       Ingress IP(s): 127.0.0.1, Service IP(s): 10.152.183.66
```

The browser uses entries in the /etc/hosts file to override what is returned by a DNS server.

Usually a charm default hostname is the application name but since Indico requires a "." in the hostname for the app to respond, so the charm configures the default to `indico.local`.

The default hostname for the Indico application is `indico.local`. To resolve it to your Ingress IP, edit [`/etc/hosts`](https://manpages.ubuntu.com/manpages/kinetic/man5/hosts.5.html) file and add the following line accordingly:

```bash
127.0.0.1 indico.local
```

Optional: run `echo "127.0.0.1 indico.local" >> /etc/hosts` to redirect the output of the command `echo` to the end of the file `/etc/hosts`.

After that, visit `http://indico.local` in a browser and you'll be presented with a screen to create an initial admin account.
