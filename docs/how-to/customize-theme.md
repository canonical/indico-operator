# How to customise theme

This charm supports providing static source files for customising Indico look and feel. [Indico's official documentation](https://docs.getindico.io/en/stable/config/settings/#customization) contains more details on the contents of those files.

If you wish to apply a set of customisation files, set the configuration option `customization_sources_url` to the URL of the git repository containing them `juju config [charm_name] customization_sources_url=[value]`. If you want the favicon to be customised too, publish it as `files/favicon.ico` in the customisation repository. For debugging purposes, you may also want to enable `customization_debug` to get meaningful log messages when the files are accessed.

The theme changes can be pulled by running the [refresh-external-resources action](https://charmhub.io/indico/actions#refresh-external-resources).

For more details on the configuration options and their default values see the [configuration reference](https://charmhub.io/indico/configurations).