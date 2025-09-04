# Deploy the Indico charm for the first time

## What you’ll do

- Deploy the [Indico charm](https://charmhub.io/indico).
- Integrate with [the Redis K8s charm](https://charmhub.io/redis-k8s) and [the PostgreSQL K8s charm](https://charmhub.io/postgresql-k8s).
- Integrate with [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/#what-is-ingress) by using [NGINX Ingress Integrator](https://charmhub.io/nginx-ingress-integrator/).

Through the process, you'll inspect the Kubernetes resources created, verify the workload state, and log in to your Indico instance.

## Requirements
- A working station, e.g., a laptop, with AMD64 architecture.
<!-- vale off -->
- Juju 3 installed and bootstrapped to a MicroK8s controller. You can accomplish this process by using a Multipass VM as outlined in this guide: [Set up your test environment](https://documentation.ubuntu.com/juju/3.6/howto/manage-your-juju-deployment/set-up-your-juju-deployment-local-testing-and-development/)
<!-- vale on -->
- NGINX Ingress Controller. If you're using [MicroK8s](https://microk8s.io/), this can be done by running the command `microk8s enable ingress`. For more details, see [Addon: Ingress](https://microk8s.io/docs/addon-ingress).

For more information about how to install Juju, see [Get started with Juju](https://documentation.ubuntu.com/juju/3.6/tutorial/).

:warning: When using a Multipass VM, make sure to replace `127.0.0.1` IP addresses with the
VM IP in steps that assume you're running locally. To get the IP address of the
Multipass instance run ```multipass info my-juju-vm```.
### Shell into the Multipass VM
> NOTE: If you're working locally, you don't need to do this step.

To be able to work inside the Multipass VM first you need to log in with the following command:
```bash
multipass shell my-juju-vm
```

### Add a Juju model for the tutorial

To manage resources effectively and to separate this tutorial's workload from
your usual work, create a new model in the MicroK8s controller using the following command:

```
juju add-model indico-tutorial
```

### Deploy the Indico charm

Since Indico requires connections to PostgreSQL and Redis, you'll deploy them too. For more information, see [Charm Architecture](https://charmhub.io/indico/docs/explanation-charm-architecture).

Redis is deployed twice because one is for the broker and the other for the cache. To do this, the `juju deploy` command accepts an extra argument with the custom application name. See more details in [`juju deploy`](https://documentation.ubuntu.com/juju/3.6/reference/juju-cli/list-of-juju-cli-commands/deploy/).

Deploy the charms:

```
juju deploy postgresql-k8s --trust
juju deploy redis-k8s redis-broker --channel=latest/edge
juju deploy redis-k8s redis-cache --channel=latest/edge
juju deploy indico
```

To see the pod created by the Indico charm, run `kubectl get pods -n indico-tutorial`, where the namespace is the name of the Juju model. The output is similar to the following:

```
NAME                             READY   STATUS    RESTARTS   AGE
indico-0                         3/3     Running   0         6h4m
```

Run [`juju status`](https://documentation.ubuntu.com/juju/3.6/reference/juju-cli/list-of-juju-cli-commands/status/) to see the current status of the deployment. In the Unit list, you can see that Indico is waiting:

```
indico/0*                 waiting   idle   10.1.74.70             Waiting for redis-broker availability
```

This means that Indico charm isn't integrated with Redis yet.

### Integrate with the Redis k8s charm the PostgreSQL k8s charm

Provide integration between Indico and Redis by running the following [`juju integrate`](https://documentation.ubuntu.com/juju/3.6/reference/juju-cli/list-of-juju-cli-commands/integrate/) commands:

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

### Integrate with Ingress by using Nginx ingress integrator charm

The NGINX Ingress Integrator charm can deploy and manage external access to HTTP/HTTPS services in a Kubernetes cluster.

If you want to make Indico charm available to external clients, you need to deploy the NGINX Ingress Integrator charm and integrate Indico with it.

See more details in [Adding the Ingress Relation to a Charm](https://charmhub.io/nginx-ingress-integrator/docs/add-the-ingress-relation).

Enable the ingress on MicroK8s first:

```
sudo microk8s enable ingress
```

Deploy the charm NGINX Ingress Integrator:

```
juju deploy nginx-ingress-integrator
```
To check if RBAC is enabled run the following command:
```
microk8s status | grep rbac
```
If it is enabled, then the output should be like the following:
```
rbac
```
If the output is empty then RBAC is not enabled.

If your cluster has RBAC enabled, you'll be prompted to run the following:
```
juju trust nginx-ingress-integrator --scope cluster
```

Run `juju status` to verify the deployment.

Provide integration between Indico and NGINX Ingress Integrator:

```
juju integrate indico nginx-ingress-integrator
```

To see the Ingress resource created, run `kubectl get ingress` on a namespace named for the Juju model you've deployed the Indico charm into. The output is similar to the following:

```
NAME                      CLASS    HOSTS             ADDRESS     PORTS   AGE
indico-local-ingress      public   indico.local   127.0.0.1   80      2d
```

Run `juju status` to see the same Ingress IP in the `nginx-ingress-integrator` message:

```
nginx-ingress-integrator                                active      1  nginx-ingress-integrator  stable    45  10.152.183.233  no       Ingress IP(s): 127.0.0.1
```

The browser uses entries in the /etc/hosts file to override what is returned by a DNS server.

Usually a charm default hostname is the application name but since Indico requires a "." in the hostname for the app to respond, so the charm configures the default to `indico.local`.

If you are deploying to a local machine you need to add the `127.0.0.1` to the `/etc/hosts` file. The default hostname for the Indico application is `indico.local`. To resolve it to your Ingress IP, edit [`/etc/hosts`](https://manpages.ubuntu.com/manpages/questing/en/man5/hosts.5.html) file and add the following line accordingly:

```
127.0.0.1 indico.local
```

Optional: run `echo "127.0.0.1 indico.local" >> /etc/hosts` to redirect the output of the command `echo` to the end of the file `/etc/hosts`.


After that, visit `http://indico.local` in a browser and you'll be presented with a screen to create an initial admin account.


## Clean up the environment

Well done! You've successfully completed the Indico tutorial. To remove the
model environment you created during this tutorial, use the following command.

```
juju destroy-model indico-tutorial --no-prompt --destroy-storage=true
```

If you used Multipass, to remove the Multipass instance you created for this tutorial, use the following command.

```
multipass delete --purge my-juju-vm
```
Finally, remove the `127.0.0.1 indico.local` line from the `/etc/hosts` file.