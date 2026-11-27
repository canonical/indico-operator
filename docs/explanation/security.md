# Security

This document explains the possible security risks in the Indico charm and best practices to avoid them. It focuses on the practices from the charm side. Refer to the [official Indico documentation](https://docs.getindico.io/en/stable/) for upstream practices.

The Indico charm is a [12-factor app charm](https://canonical.com/juju/docs/12-factor/latest/) built with the Flask framework extension. Part of the charm's security posture, such as how secrets, ingress, and the workload container are handled, depends on the 12-factor framework and tooling. Refer to the [12-factor app support documentation](https://canonical.com/juju/docs/12-factor/latest/) and the [Juju security documentation](https://canonical.com/juju/docs/juju-cli/3.6/explanation/juju-security/) for the security practices that apply to all 12-factor charms.

## Outdated software

Outdated software components, such as the charm, the Indico rock, the bundled plugins, or the 12-factor framework, can introduce exploitable security vulnerabilities.

### Best practices

- Regularly update the charm revision to include the latest charm components. Updates include security fixes from the dependencies, the Indico workload, and the 12-factor framework, as the charm dependencies are regularly updated.
- Regularly update Juju to the latest version to include security fixes.
- Deploy observability, like the [Canonical Observability Stack](https://charmhub.io/topics/canonical-observability-stack), to detect any unusual behaviors.

## Loss of data

The Indico database or the uploaded files can be lost or corrupted for various reasons.

### Best practices

- Use S3 for uploaded files and static content, and back up the bucket regularly. See [How to configure S3](../how-to/configure-s3.md).
- Use a dedicated Charmed PostgreSQL and regularly back up the database through the charm's [backup action](https://canonical.com/data/postgresql/docs/14/how-to/back-up-and-restore/create-a-backup/).

## Unencrypted traffic

If Indico is served over HTTP, the traffic between Indico and its users is unencrypted, risking eavesdropping and tampering. Unencrypted email traffic carries the same risk.

### Best practices

- Integrate the Indico charm with an ingress that provides TLS, such as [NGINX Ingress Integrator](https://charmhub.io/nginx-ingress-integrator).
- If you set the [`site_url`](https://charmhub.io/indico/configurations#site_url) configuration option, use an `https://` URL. See [How to configure the external hostname](../how-to/configure-the-external-hostname.md).
- Encrypt the SMTP connection by setting the [`transport_security`](https://charmhub.io/smtp-integrator/configurations#transport_security) configuration option of the SMTP Integrator charm to `starttls` or `tls`. See [How to configure SMTP](../how-to/configure-smtp.md).

## Authentication and access control

Weak or incorrectly configured authentication increases the risk of unauthorized access to events, registrations, and the personal data of participants.

### Best practices

- Integrate the charm with a single sign-on (SSO) identity provider through the `saml` or `oauth` integration to centralize authentication and enforce your organization's login policies. See [How to configure SAML](../how-to/configure-saml.md).
- Once SSO is in place and at least one administrator can log in through it, set the [`local-identities`](https://charmhub.io/indico/configurations#local-identities) configuration option to `false`. This setting disables the built-in username and password login.
- Limit the use of the [`add-admin`](https://charmhub.io/indico/actions#add-admin) action to the users who strictly require administrative privileges. Juju records action parameters, including the password, in the controller, so change the password of the new administrator after the first login.

## Third-party plugins

Plugins installed through the [`external_plugins`](https://charmhub.io/indico/configurations#external_plugins) configuration option run inside the Indico workload with the same privileges as Indico itself. A malicious or compromised plugin can access the database, the uploaded files, and the secrets available to the workload.

### Best practices

- Only install plugins from sources you trust, such as the [official Indico plugins](https://github.com/indico/indico-plugins). See [How to install plugins](../how-to/install-plugins.md).
- Pin plugins to a specific version or Git commit so that a redeployment or the `refresh-external-resources` action doesn't install code you haven't reviewed.
- Use the [`pip-index-url`](https://charmhub.io/indico/configurations#pip-index-url) configuration option to install plugins from an internal, vetted package mirror instead of the public PyPI index.
- Only enable the plugins you need through the [`enabled-plugins`](https://charmhub.io/indico/configurations#enabled-plugins) configuration option.

## Secret management

Indico uses the Flask secret key to sign session cookies and other security-sensitive tokens. If the key leaks, an attacker can forge sessions and impersonate users.

### Best practices

- Store the secret key in a [Juju user secret](https://canonical.com/juju/docs/juju-cli/3.6/reference/secret/) and pass it to the charm through the [`secret-key`](https://charmhub.io/indico/configurations#secret-key) configuration option. Grant the secret only to the Indico application.
- Rotate the secret key if you suspect it has been exposed. Rotating the key invalidates existing user sessions.
- Refer to the [secrets section of the Flask framework extension](https://canonical.com/juju/docs/charmcraft/4/reference/extensions/flask-framework-extension/#flask-framework-extension-secrets) for details on how the 12-factor framework passes Juju secrets to the workload.

## Personal data

Indico stores personal data of users and event participants, such as names, email addresses, and affiliations. Keeping this data longer than required increases the impact of a data breach and can conflict with data protection regulations such as the GDPR.

### Best practices

- Use the [`anonymize-user`](https://charmhub.io/indico/actions#anonymize-user) action to anonymize the stored personal data of users who request it.
- Restrict access to the database and S3 backups to the people who need it, as backups contain the same personal data as the live deployment.
