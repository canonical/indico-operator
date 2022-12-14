This charm supports providing static source files for customizing Indico look and feel. Details on how those files should look like can be consulted in [Indico's official documentation](https://docs.getindico.io/en/stable/config/settings/#customization).

If you wish to apply a set of customization files, set the configuration option `customization_sources_url` to the URL of the git repository containing them `juju config [charm_name] customization_sources_url=[value]`. For debugging purposes, you may also want to enable `customization_debug` to get meaningful log messages when the files are accessed.

The theme changes can be pulled by running the [refresh-external-resources action](https://charmhub.io/indico/actions#refresh-external-resources).

For more details on the configuration options and their default values see the [configuration reference](https://charmhub.io/indico/configure).
