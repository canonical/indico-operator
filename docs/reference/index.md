# Reference

Technical specifications and descriptions for the Indico charm's configuration surfaces,
integration interfaces, extensibility mechanisms, and runtime behavior within a
Juju-managed Kubernetes environment.

## Charm configuration and operations
<!--
Themes: charm lifecycle, configuration options, operational actions
Justification: core charm machinery — configuration, actions, and architectural internals
User journey context: all stages (lookup-driven)
Juju ecosystem scope: charm-specific (configuration, actions), cross-charm (relation events)
-->

- [Actions](actions.md)
- [Configurations](configurations.md)
- [Charm architecture](charm-architecture.md)

## Extensibility
<!--
Themes: plugin architecture, theme customization, external resources
Justification: shared concern — extending Indico functionality beyond defaults
User journey context: configuration, post-deployment customization
Juju ecosystem scope: charm-specific (configuration options)
-->

- [Plugins](plugins.md)
- [Theme customization](theme-customization.md)

## Networking and integrations
<!--
Themes: relation interfaces, external network access, ingress
Justification: shared concern — connectivity between charm and external systems
User journey context: integration, scaling, troubleshooting
Juju ecosystem scope: cross-charm (relation endpoints), model-level (ingress/networking)
-->

- [Integrations](integrations.md)
- [External access](external-access.md)
