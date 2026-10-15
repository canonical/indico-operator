# Deploy the Indico charm for the first time

## What you’ll do

- Deploy the [Indico charm](https://charmhub.io/indico).
- Integrate with [the Redis K8s charm](https://charmhub.io/redis-k8s) and [the PostgreSQL K8s charm](https://charmhub.io/postgresql-k8s).
- Expose Indico by using [Gateway API Integrator](https://charmhub.io/gateway-api-integrator) and [Ingress Configurator](https://charmhub.io/ingress-configurator).

Through the process, you'll inspect the Kubernetes resources created, verify the workload state, and log in to your Indico instance.

## Requirements
- A working station, e.g., a laptop, with AMD64 architecture.
- [Multipass](https://canonical.com/multipass) installed.

### Set up the environment

Launch a Multipass VM and log into it:

```
multipass launch 24.04 --name indico-tutorial --cpus 4 --memory 8G --disk 50G
multipass shell indico-tutorial
```

Inside the VM, use [Concierge](https://github.com/canonical/concierge) to install Juju and [Canonical Kubernetes](https://ubuntu.com/kubernetes), and bootstrap a controller:

```
sudo snap install --classic concierge
sudo concierge prepare -p k8s
```

Configure the Kubernetes load balancer to use the VM IP address:

```
PREFSRC=$(ip -4 -j route get 2.2.2.2 | jq -r '.[] | .prefsrc')
sudo k8s set load-balancer.cidrs=$PREFSRC/32
```

### Add a Juju model for the tutorial

To manage resources effectively and to separate this tutorial's workload from
your usual work, create a new model in the Kubernetes controller using the following command:

```
juju add-model indico-tutorial
```

### Deploy the Indico charm

Since Indico requires connections to PostgreSQL and Redis, you'll deploy them too. For more information, see [Charm Architecture](https://charmhub.io/indico/docs/explanation-charm-architecture).

Redis is deployed twice because one is for the broker and the other for the cache. To do this, the `juju deploy` command accepts an extra argument with the custom application name. See more details in [`juju deploy`](https://canonical.com/juju/docs/juju-cli/3.6/reference/juju-cli/list-of-juju-cli-commands/deploy/).

Deploy the charms:

```
juju deploy postgresql-k8s --channel=14/stable --trust
juju deploy redis-k8s redis-broker --channel=latest/edge
juju deploy redis-k8s redis-cache --channel=latest/edge
juju deploy indico
```

To see the pod created by the Indico charm, run `kubectl get pods -n indico-tutorial`, where the namespace is the name of the Juju model. The output is similar to the following:

```
NAME                             READY   STATUS    RESTARTS   AGE
indico-0                         3/3     Running   0         6h4m
```

Run [`juju status`](https://canonical.com/juju/docs/juju-cli/3.6/reference/juju-cli/list-of-juju-cli-commands/status/) to see the current status of the deployment. In the Unit list, you can see that Indico is waiting:

```
indico/0*                 waiting   idle   10.1.74.70             Waiting for redis-broker availability
```

This means that Indico charm isn't integrated with Redis yet.

### Integrate with the Redis k8s charm the PostgreSQL k8s charm

Provide integration between Indico and Redis by running the following [`juju integrate`](https://canonical.com/juju/docs/juju-cli/3.6/reference/juju-cli/list-of-juju-cli-commands/integrate/) commands:

```
juju integrate indico:redis-broker redis-broker
juju integrate indico:redis-cache redis-cache
```

Run `juju status` to see that the message has changed:

```
indico/0*                 waiting   idle   10.1.74.70             Waiting for database availability
```

Provide integration between Indico and PostgreSQL:

```
juju integrate indico postgresql-k8s:database
```

Note: `database` is the name of the integration. This is needed because establishes that the two charms are compatible with each other.  You can run `juju info indico` to check what are the integration names required by the Indico application.

Enable PostgreSQL extensions:

```
juju config postgresql-k8s plugin_pg_trgm_enable=true plugin_unaccent_enable=true
```


Run `juju status` and wait until the Application status is `Active` as the following example:

Optional: run `juju status --relations --watch 5s` to watch the status every five seconds with the Relations section.

```
App                       Version                       Status  Scale  Charm                     Channel  Rev  Address         Exposed  Message
indico                 3.3                           active      1  indico                              182  10.152.183.68   no
```

The deployment finishes when the status shows "Active" for all charms.

### Expose Indico by using Gateway API Integrator and Ingress Configurator

The Gateway API Integrator charm manages external access to HTTP/HTTPS services in a Kubernetes cluster through the [Gateway API](https://gateway-api.sigs.k8s.io/). The Ingress Configurator charm passes the ingress configuration, such as the hostname, to it.

Deploy Gateway API Integrator and configure it to use the Cilium gateway class provided by Canonical Kubernetes:

```
juju deploy gateway-api-integrator --trust --channel=1/stable
juju config gateway-api-integrator gateway-class=cilium
```

Gateway API Integrator requires a TLS certificate provider. Deploy the Self Signed Certificates charm and integrate it:

```
juju deploy self-signed-certificates --channel=1/stable
juju integrate gateway-api-integrator self-signed-certificates
```

Deploy Ingress Configurator and set the hostname. Indico requires a "." in the hostname for the app to respond, so use `indico.local`:

```
juju deploy ingress-configurator --trust
juju config ingress-configurator hostname=indico.local paths=/
```

Provide integration between Indico, Ingress Configurator and Gateway API Integrator:

```
juju integrate gateway-api-integrator ingress-configurator
juju integrate indico ingress-configurator
```

Run `juju status` and wait until all applications are `active`. Then verify that Indico responds:

```
curl -k --resolve indico.local:443:$PREFSRC https://indico.local
```

Optional: to access Indico from a browser on your host machine, get the Multipass VM IP by running `multipass info indico-tutorial`. Then, on the host machine, edit [`/etc/hosts`](https://manpages.ubuntu.com/manpages/noble/man5/hosts.5.html) and add the following line, replacing `<multipass vm ip>` with the VM IP:

```
<multipass vm ip> indico.local
```

After that, visit `https://indico.local` in a browser, accept the self-signed certificate, and you'll be presented with a screen to create an initial admin account.


## Clean up the environment

Well done! You've successfully completed the Indico tutorial. To remove the
model environment you created during this tutorial, use the following command.

```
juju destroy-model indico-tutorial --no-prompt --destroy-storage=true
```

To remove the Multipass instance you created for this tutorial, run the following command on the host machine.

```
multipass delete --purge indico-tutorial
```
If you edited the host `/etc/hosts` file, remove the `<multipass vm ip> indico.local` line.
