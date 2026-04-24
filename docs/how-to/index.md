# How-to guides

Task-oriented procedures for configuring integrations, managing network access,
customizing Indico's appearance and functionality, and handling operational tasks
like redeployment and development contributions.

## Integration
<!--
Themes: external service integration, authentication, storage, email
Justification: shared operational concern — connecting Indico to external services via Juju relations
User journey context: configuration, integration phase
Juju ecosystem scope: cross-charm (relation integration with S3, SAML, SMTP integrators)
-->

- [Configure S3](configure-s3.md)
- [Configure SAML](configure-saml.md)
- [Configure SMTP](configure-smtp.md)

## Networking and access
<!--
Themes: proxy configuration, external hostname, ingress
Justification: shared concern — network-level configuration for external connectivity
User journey context: configuration, initial setup
Juju ecosystem scope: model-level (proxy), cross-charm (ingress integration)
-->

- [Configure a proxy](configure-a-proxy.md)
- [Configure the external hostname](configure-the-external-hostname.md)

## Customization
<!--
Themes: plugin installation, theme modification, extensibility
Justification: shared concern — extending and personalizing Indico's default behavior
User journey context: post-deployment, configuration
Juju ecosystem scope: charm-specific (configuration options, actions)
-->

- [Install plugins](install-plugins.md)
- [Customize theme](customize-theme.md)

## Maintenance and development
<!--
Themes: redeployment/migration, development contribution, charm lifecycle
Justification: shared operational concern — sustaining and evolving the charm beyond initial deployment
User journey context: maintenance, development
Juju ecosystem scope: charm-specific (redeployment), model-level (migration), cross-charm (testing integrations)
-->

- [Redeploy](redeploy.md)
- [Contribute](contribute.md)