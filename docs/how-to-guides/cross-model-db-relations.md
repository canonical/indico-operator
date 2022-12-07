# Cross-model DB relations

In some settings it can be useful to deploy the database (PostgreSQL) in a different cloud, for example LXD or OpenStack, and integrate Indico with it via cross-model relations. First, create a suitable model on the cloud of your choice:

```
juju switch database
juju deploy postgresql
juju offer postgresql:db
```

In most k8s deployments, traffic to external services from worker pods will be SNATed by some part of the infrastructure. You will need to know what the source addresses or address range is for the next step.

```
juju switch indico-test # assuming you've deployed Indico into a k8s model called "indico-test"
juju find-offers  # note down offer URL; example used below:
```

It’s also possible you’ll need to grant specific access to the user you want to join the relation from. If you don’t see any output from the `find-offers` command, and run `juju whoami` to confirm your account name and then from the PostgreSQL model run `juju grant ${user} consume ${offer-url}`. Once you have something showing up in the output of `juju find-offers` you can proceed to the next step.

```
juju relate indico admin/database.postgresql --via 10.9.8.0/24
```

(In the case of postgresql, `--via` is needed so that the charm can configure `pga_hba.conf` to let the k8s pods connect to the database.)
