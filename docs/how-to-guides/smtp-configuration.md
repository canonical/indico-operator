# SMTP configuration

To configure Indico's SMTP you'll have to set the following configuration options with the appropriate values for your SMTP server by running `juju config [charm_name] [configuration]=[value]`.

Set `smtp_server`to the SMTP server IP or hostname, `smtp_port` for the SMTP sever port if different from the default. If authentication is needed, the credentials can be set with `smtp_login`and `smtp_password`. Note that TLS can be turned on and off with `smtp_use_tls`.

This charm exposes the appropriate configuration to modify the sender address for the emails sent by Indico. For emails you do not with the users to reply to, the sender can be set with `indico_no_reply_email`. The public support emails show in the 'Contact' page can be set via `indico_public_support_email` and the technical support email, via `indico_support_email`.

For more details on the configuration options and their default values see the [configuration reference](https://charmhub.io/indico/configure).
