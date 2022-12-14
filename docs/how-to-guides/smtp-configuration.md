To configure Indico's SMTP you'll have to set the following configuration options with the appropriate values for your SMTP server by running `juju config [charm_name] [configuration]=[value]`.

Set `smtp_server`to the SMTP server IP or hostname, `smtp_port` for the SMTP sever port if different from the default.

If authentication is needed, the credentials can be set with `smtp_login`and `smtp_password`.

If needed, the TLS can be turned on and off with `smtp_use_tls`.

For more details on the configuration options and their default values see the [configuration reference](https://charmhub.io/indico/configure).
