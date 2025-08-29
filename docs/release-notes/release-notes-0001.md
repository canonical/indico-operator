<!-- Remember to update this file for your charm!! -->

# Indico release notes – latest/stable

These release notes cover new features and changes in Indico for revisions
234-266 between the dates of 2024-10-25 and 2025-08-28.

Main features:

* Bumped Indico version to 3.3.6 and Paypal-payment plugin to 3.3.2.


Main breaking changes:



Main bug fixes:


See our [Release policy and schedule](docs/release-notes/landing-page.md).

## Requirements and compatibility

<!--
Specify the workload version; link to the workload's release notes if available.
Add information about the requirements for this charm in the table
below, for instance, a minimum Juju version. 
If the user will need any specific upgrade instructions for this
release, include those instructions here.
-->

The charm operates <workload name with version>.

The table below shows the required or supported versions of the software necessary to operate the charm.

| Software                | Required version |
|-------------------------|------------------|
| Juju                    | XXXX             |
| Terraform               | XXXX             |
| Terraform Juju provider | XXXX             |
| Ubuntu                  | XXXX             |
| XXXX                    | XXXX             |

## Updates

The following major and minor features were added in this release.

### Added Service Health Grafana dashboard
Added a Grafana dashboard to verify Indico Service Health.
The dashboard is based on the four golden signals, making it easier to troubleshoot issues and assess system performance.

<Add more context and information about the entry>

Relevant links:
* [PR](https://github.com/canonical/indico-operator/pull/622)
* [Related documentation]()
* [Related issue]()


### Updated nginx-prometheus-exporter to 1.4.2 in Indico NGINX Rock
Updating the nginx-prometheus-exporter to 1.4.2 in the Indico NGINX Rock charm along with adding xmlsec library to the Indico rock.

<Add more context and information about the entry>

Relevant links:
* [PR](https://github.com/canonical/indico-operator/pull/648)
* [Related documentation]()
* [Related issue]()


### Validated SQA CharmQA metadata.yaml based on charm behavior
Properly sets the interface optional flag on the metadata.yaml file to reflect the actual charms behavior.
This is part of an initiative modelling how charms should expose the metadata to Juju and the Charmhub store in order to be eligible for automated testing as part of this initiative.

<Add more context and information about the entry>

Relevant links:
* [PR](https://github.com/canonical/indico-operator/pull/480)
* [Related documentation]()
* [Related issue]()


### Bumped Indico version to 3.3.6 and Paypal-payment plugin to 3.3.2
Bumping the indico version from 3.3.1 to ( 3.3.6 ). This bumps the paypal-payment plugin from 3.3 to 3.3.2 as well.
Indico released new version with security updates. This change ensures we have them.

<Add more context and information about the entry>

Relevant links:
* [PR](https://github.com/canonical/indico-operator/pull/640)
* [Related documentation]()
* [Related issue]()


### Added Indico terraform module
Add Indico terraform module, tests and changes Renovate for updating the test and the provider versions.

<Add more context and information about the entry>

Relevant links:
* [PR](https://github.com/canonical/indico-operator/pull/653)
* [Related documentation]()
* [Related issue]()


### Updated the rock base and pinned websockets version
Updated the indico-nginx-rock base, updated the nginx-prometheus-exporter from a snap to source. Pinned the websockets version.
<Add more context and information about the entry>

Relevant links:
* [PR](https://github.com/canonical/indico-operator/pull/466)
* [Related documentation]()
* [Related issue]()







## Bug fixes

* Pinned boto3 version to 1.35.99 to fix S3 storage issue ([PR](https://github.com/canonical/indico-operator/pull/645)).





## Known issues

<!--
Add a bulleted list with links to unresolved issues – the most important/pressing ones,
the ones being worked on currently, or the ones with the most visibility/traffic.
You don’t need to add links to all the issues in the repository if there are
several – a list of 3-5 issues is sufficient. 
If there are no known issues, keep the section and write "No known issues".
-->

## Thanks to our contributors

<!--
List of contributors based on PRs/commits. Remove this section if there are no contributors in this release.
-->

[amandahla](https://github.com/amandahla), [moisesbenzan](https://github.com/moisesbenzan), [srbouffard](https://github.com/srbouffard), [DeeKay3](https://github.com/DeeKay3), [alithethird](https://github.com/alithethird), [swetha1654](https://github.com/swetha1654)