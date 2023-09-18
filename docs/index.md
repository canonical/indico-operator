A [Juju](https://juju.is/) [charm](https://juju.is/docs/olm/charmed-operators) deploying and managing [Indico](https://getindico.io/) on Kubernetes. Indico is an open-source tool for event organisation, archival and collaboration.

This charm simplifies initial deployment and "day N" operations of Indico on Kubernetes, such as scaling the number of instances, integration with SSO, access to S3 for redundant file storage and more. It allows for deployment on many different Kubernetes platforms, from [MicroK8s](https://microk8s.io) to [Charmed Kubernetes](https://ubuntu.com/kubernetes) and public cloud Kubernetes offerings.

As such, the charm makes it easy for those looking to take control of their own events management system whilst keeping operations simple, and gives them the freedom to deploy on the Kubernetes platform of their choice.

For DevOps or SRE teams this charm will make operating Indico simple and straightforward through Juju's clean interface. It will allow easy deployment into multiple environments for testing of changes, and supports scaling out for enterprise deployments.

## Contributing to this documentation

Documentation is an important part of this project, and we take the same open-source approach to the documentation as the code. As such, we welcome community contributions, suggestions and constructive feedback on our documentation. Our documentation is hosted on the [Charmhub forum](https://discourse.charmhub.io/t/indico-documentation-overview/7571) to enable easy collaboration. Please use the "Help us improve this documentation" links on each documentation page to either directly change something you see that's wrong, ask a question, or make a suggestion about a potential change via the comments section.

If there's a particular area of documentation that you'd like to see that's missing, please [file a bug](https://github.com/canonical/indico-operator/issues).

## In this documentation

| | |
|--|--|
|  [Tutorials](https://charmhub.io/indico/docs/tutorial-getting-started)</br>  Get started - a hands-on introduction to using the Charmed Indico operator for new users </br> |  [How-to guides](https://charmhub.io/indico/docs/how-to-configure-a-proxy) </br> Step-by-step guides covering key operations and common tasks |
| [Reference](https://charmhub.io/indico/docs/reference-actions) </br> Technical information - specifications, APIs, architecture | [Explanation](https://charmhub.io/indico/docs/explanation-charm-architecture) </br> Concepts - discussion and clarification of key topics  |
