# LDAP configuration

To configure Indico's LDAP integration you'll have to set `ldap_host` with the URL for your LDAP server by running `juju config [charm_name] ldap_host=[value]` and `ldap_password` with its credentials `juju config [charm_name] ldap_password=[value]`.

For more details on the configuration options and their default values see the [configuration reference](https://charmhub.io/indico/configure).
