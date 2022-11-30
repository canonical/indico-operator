# Refreshing external resources

To refresh external resources, which includes themes and customization sources, use the `refresh-external-resources` action provided by this charm. You'll need to run this action against each unit in your application.

Note that if those resources include python packages from a git repository, the version number has to be incremented for the change to take effect. The git repository needs to be reachable from the unit.

For example, if you have two units (`indico/0` and `indico/1`) you would run:
```
juju run-action --wait indico/0 indico/1 refresh-external-resources
```

To configure the external resources, run the following command:
```
juju config indico customization_sources_url=https://github.com/myindico/myindico-example-files.git
```
