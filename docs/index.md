# Indico Operator

A [Juju](https://juju.is/) [charm](https://juju.is/docs/olm/charmed-operators) deploying and managing [Indico](https://getindico.io/) on Kubernetes. Indico is an open-source tool for event organisation, archival, and collaboration.

Like any Juju charm, this charm supports one-line deployment, configuration, integration, scaling, and more. For Indico, this includes:
- Integrations with SSO
- Access to S3

The Indico charm allows for deployment on many different Kubernetes platforms, from [MicroK8s](https://microk8s.io) to [Charmed Kubernetes](https://ubuntu.com/kubernetes) and public cloud Kubernetes offerings.

As such, the charm makes it easy for those looking to take control of their own events management system whilst keeping operations simple and gives them the freedom to deploy on the Kubernetes platform of their choice.

This charm will make operating Indico simple and straightforward for DevOps or SRE teams through Juju's clean interface. It will allow easy deployment into multiple environments to test changes and support scaling out for enterprise deployments.

## In this documentation

| | |
|--|--|
|  [Tutorials](https://charmhub.io/indico/docs/tutorial)</br>  Get started - a hands-on introduction to using the Charmed Indico operator for new users </br> |  [How-to guides](https://charmhub.io/indico/docs/how-to-configure-a-proxy) </br> Step-by-step guides covering key operations and common tasks |
| [Reference](https://charmhub.io/indico/docs/reference-actions) </br> Technical information - specifications, APIs, architecture | [Explanation](https://charmhub.io/indico/docs/explanation-charm-architecture) </br> Concepts - discussion and clarification of key topics  |

## Contributing to this documentation

Documentation is an important part of this project, and we take the same open-source approach to the documentation as the code. As such, we welcome community contributions, suggestions and constructive feedback on our documentation. Our documentation is hosted on the [Charmhub forum](https://discourse.charmhub.io/t/indico-documentation-overview/7571) to enable easy collaboration. Please use the "Help us improve this documentation" links on each documentation page to either directly change something you see that's wrong, ask a question, or make a suggestion about a potential change via the comments section.

If there's a particular area of documentation that you'd like to see that's missing, please [file a bug](https://github.com/canonical/indico-operator/issues).

## Project and community

The Indico Operator is a member of the Ubuntu family. It's an open-source project that warmly welcomes community projects, contributions, suggestions, fixes, and constructive feedback.

- [Code of conduct](https://ubuntu.com/community/code-of-conduct)
- [Get support](https://discourse.charmhub.io/)
- [Join our online chat](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)
- [Contribute](Contribute)

Thinking about using the Indico Operator for your next project? [Get in touch](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)!

# Contents

1. [Tutorial](tutorial.md)
1. [How to](how-to)
  1. [Configure a proxy](how-to/configure-a-proxy.md)
  1. [Configure S3](how-to/configure-s3.md)
  1. [Configure SAML](how-to/configure-saml.md)
  1. [Configure SMTP](how-to/configure-smtp.md)
  1. [Configure the external hostname](how-to/configure-the-external-hostname.md)
  1. [Install plugins](how-to/install-plugins.md)
  1. [Customize theme](how-to/customize-theme.md)
  1. [How to redeploy](how-to/redeploy.md)
  1. [Contribute](how-to/contribute.md)
1. [Reference](reference)
  1. [Actions](reference/actions.md)
  1. [Configurations](reference/configurations.md)
  1. [External access](reference/external-access.md)
  1. [Integrations](reference/integrations.md)
  1. [Plugins](reference/plugins.md)
  1. [Theme customization](reference/theme-customization.md)
1. [Explanation](explanation)
  1. [Charm architecture](explanation/charm-architecture.md)