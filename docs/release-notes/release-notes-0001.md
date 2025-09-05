# Indico release notes – latest/stable

These release notes cover new features and changes in Indico for revisions
234-266 between the dates of 2024-10-25 and 2025-08-28.

Main features:

* Bumped Indico version to 3.3.6 and paypal-payment plugin to 3.3.2.


See our [Release policy and schedule](docs/release-notes/landing-page.md).

## Requirements and compatibility

The charm operates Indico 3.3.6.

The table below shows the required or supported versions of the software necessary to operate the charm.

| Software                | Required version |
|-------------------------|------------------|
| Juju                    | 3.x              |
| Terraform               | >=1.12           |
| Terraform Juju provider | >=0.21           |
| Ubuntu                  | >=20.04          |

## Updates

The following major and minor features were added in this release.

### Added Service Health Grafana dashboard

We added a Grafana dashboard to verify Indico Service Health.
The dashboard is based on the four golden signals, making it easier to troubleshoot issues and assess system performance.

Relevant links:

* [PR](https://github.com/canonical/indico-operator/pull/622)

### Updated `nginx-prometheus-exporter` to 1.4.2 in Indico NGINX Rock

The `nginx-prometheus-exporter` was updated to 1.4.2 in the Indico NGINX Rock charm,
and the `xmlsec` library was added to the Indico rock.

Relevant links:

* [PR](https://github.com/canonical/indico-operator/pull/648)

### Validated SQA CharmQA metadata.yaml based on charm behavior

Now the optional `interface` flag is properly set in the `metadata.yaml` file to reflect the actual charm's behavior.
This is part of an initiative modelling how charms should expose the metadata to Juju and the Charmhub store in order to be eligible for automated testing as part of this initiative.

Relevant links:

* [PR](https://github.com/canonical/indico-operator/pull/480)

### Bumped Indico version to 3.3.6 and `paypal-payment` plugin to 3.3.2

The Indico version was bumped from 3.3.1 to 3.3.6. The `paypal-payment` plugin was bumped
from 3.3 to 3.3.2 as well. As Indico released a new version with security updates, this
version bump ensures we also have the updates.

Relevant links:

* [PR](https://github.com/canonical/indico-operator/pull/640)

### Added Indico Terraform module

The Indico charm now has a Terraform module. We also updated the tests and provider versions.

Relevant links:

* [PR](https://github.com/canonical/indico-operator/pull/653)

### Updated the rock base and pinned websockets version

We updated the `indico-nginx-rock` base, updated the `nginx-prometheus-exporter` from a snap to source, and pinned the websockets version.

Relevant links:

* [PR](https://github.com/canonical/indico-operator/pull/466)

## Bug fixes

* Pinned `boto3` version to 1.35.99 to fix S3 storage issue ([PR](https://github.com/canonical/indico-operator/pull/645)).

## Known issues

No known issues.

## Thanks to our contributors

[amandahla](https://github.com/amandahla), [moisesbenzan](https://github.com/moisesbenzan), [srbouffard](https://github.com/srbouffard), [DeeKay3](https://github.com/DeeKay3), [alithethird](https://github.com/alithethird), [swetha1654](https://github.com/swetha1654)
