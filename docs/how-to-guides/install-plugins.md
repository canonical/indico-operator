This charm supports installing both official and custom plugins for Indico, from pypi and from a git repositories.

The following plugins are already packed as part of the charm `piwik` and `storage-s3`. The list of available official plugins can be found [here](https://github.com/indico/indico-plugins).

To install additional plugins, provide the configuration `external_plugins` as a comma separated list with the desired packages to be installed. Each element should be compatible with pip:  e.g. `juju config [charm_name] external_plugins=git+https://github.com/indico/indico-plugins-cern.git/#subdirectory=themes_cern,indico-plugin-themes-legacy`.

The installed plugins can be upgraded by running the [refresh-external-resources action](https://charmhub.io/indico/actions#refresh-external-resources). Note that the upgrade won't take place if the publish version hasn't changed.

For more details on the configuration options and their default values see the [configuration reference](https://charmhub.io/indico/configure).