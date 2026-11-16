# Contributing

This document explains the processes and practices recommended for contributing enhancements to the Indico charm.

## Overview

- Generally, before developing enhancements to this charm, you should consider [opening an issue
  ](https://github.com/canonical/indico-operator/issues) explaining your use case.
- If you would like to chat with us about your use-cases or proposed implementation, you can reach
  us at [Canonical Matrix public channel](https://matrix.to/#/#charmhub-charmdev:ubuntu.com)
  or [Discourse](https://discourse.charmhub.io/).
- Familiarizing yourself with the [Juju documentation](https://documentation.ubuntu.com/juju/3.6/howto/manage-charms/)
  will help you a lot when working on new features or bug fixes.
- All enhancements require review before being merged. Code review typically examines
  - code quality
  - test coverage
  - user experience for Juju operators of this charm.
- Once your pull request is approved, we squash and merge your pull request branch onto
  the `main` branch. This creates a linear Git commit history.
- For further information on contributing, please refer to our
  [Contributing Guide](https://github.com/canonical/is-charms-contributing-guide).

## Code of conduct

When contributing, you must abide by the
[Ubuntu Code of Conduct](https://ubuntu.com/community/ethos/code-of-conduct).

## Security

To report a vulnerability, follow the process in [SECURITY.md](SECURITY.md).
Do not open a public issue for security problems.

## Changelog and release notes

### Changelog

Document any user-relevant change in [docs/changelog.md](docs/changelog.md)
in the format of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Use the date of the contribution as the header for new entries.

### Release notes

Every user-relevant change also ships with a release-note artifact:

- Copy
  [`docs/release-notes/template/_change-artifact-template.yaml`](docs/release-notes/template/_change-artifact-template.yaml)
  to `docs/release-notes/artifacts/pr<NNNN>.yaml`, where `<NNNN>` is your pull
  request number padded to four digits (`pr0707.yaml` for PR #707), and fill
  it in.
- If your change is not user-relevant, add the `no-release-note` label to the
  pull request instead.

The "Check for release notes artifact" workflow enforces this on every pull
request.

To publish the release notes for a release:

1. Copy
   [`docs/release-notes/template/_release-artifact-template.yaml`](docs/release-notes/template/_release-artifact-template.yaml)
   to `docs/release-notes/releases/release<NNNN>.yaml`, where `<NNNN>` is the
   next release number, and fill it in, listing the change artifacts the
   release includes and the revision and date ranges. Set `highlight: true`
   in the change artifacts that belong under "Main features".
2. Merge it to `main`. The "Create release notes" workflow renders
   `docs/release-notes/release-notes-<NNNN>.md` from
   `docs/release-notes/template/release-template.md.j2` and opens a pull
   request with the page.
3. In that pull request, review the page, list any known issues, and add it to
   the [release notes landing page](docs/release-notes/landing-page.md).

## Submissions

If you want to address an issue or a bug in this project,
notify in advance the people involved to avoid confusion;
also, reference the issue or bug number when you submit the changes.

- [Fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/about-forks)
  our [GitHub repository](https://github.com/canonical/indico-operator)
  and add the changes to your fork, properly structuring your commits,
  providing detailed commit messages and signing your commits.
- Make sure the updated project builds and runs without warnings or errors;
  this includes linting, documentation, code and tests.
- Submit the changes as a
  [pull request (PR)](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork).

Your changes will be reviewed in due time; if approved, they will be eventually merged.

### Signing commits

To improve contribution tracking,
we use the [Canonical contributor license agreement](https://assets.ubuntu.com/v1/ff2478d1-Canonical-HA-CLA-ANY-I_v1.2.pdf)
(CLA) as a legal sign-off, and we require all commits to have verified signatures.

#### Canonical contributor agreement

Canonical welcomes contributions to the Indico charm. Please check out our
[contributor agreement](https://ubuntu.com/legal/contributors) if you're interested in contributing to the solution.

The CLA sign-off is simple line at the
end of the commit message certifying that you wrote it
or have the right to commit it as an open-source contribution.

#### Verified signatures on commits

All commits in a pull request must have cryptographic (verified) signatures.
To add signatures on your commits, follow the
[GitHub documentation](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits).

## Develop

To make contributions to this charm, you'll need a working
[development setup](https://documentation.ubuntu.com/juju/latest/howto/manage-your-juju-deployment/set-up-your-juju-deployment-local-testing-and-development/).

The code for this charm can be downloaded as follows:

```bash
git clone https://github.com/canonical/indico-operator
```

Install `tox` to run the checks:

```bash
pip install tox
```

You can use the environments created by `tox` for development:

```bash
tox --notest -e unit
source .tox/unit/bin/activate
```

### Test

This project uses `tox` for managing test environments. There are some pre-configured environments
that can be used for linting and formatting code when you're preparing contributions to the charm:

* `tox`: Executes all of the basic checks and tests (`format`, `lint`, `unit`, `static`, and `coverage-report`).
* `tox -e format`: Runs formatting using `ruff`.
* `tox -e lint`: Runs a range of static code analysis to check the code.
* `tox -e static`: Runs other checks such as `bandit` for security issues.
* `tox -e unit`: Runs the unit tests.
* `tox -e integration`: Runs the integration tests.

The integration tests need a Juju controller on Kubernetes and the Indico rock
image (see below); they also run in CI on every pull request.

### Build the rock and charm

Use [Rockcraft](https://documentation.ubuntu.com/rockcraft/stable/) to create the
OCI image for Indico, and then upload the image to a local registry,
which stores OCI archives so they can be downloaded and deployed.

Set up [Canonical Kubernetes](https://documentation.ubuntu.com/canonical-kubernetes/latest/)
and Juju with [Concierge](https://github.com/canonical/concierge), using
its `k8s` preset:

```bash
sudo snap install concierge --classic
sudo concierge prepare --preset k8s
```

Canonical Kubernetes has no built-in registry, so start a local one. The
cluster pulls from `localhost` over plain HTTP:

```bash
docker run -d --restart always -p 5000:5000 --name registry registry:2
```

The following commands pack the OCI image and push it into
the local registry:

```bash
cd indico_rock
rockcraft pack
rockcraft.skopeo --insecure-policy copy --dest-tls-verify=false oci-archive:indico_3.3.12_amd64.rock docker://localhost:5000/indico:latest
```

Build the charm in this git repository using:

```bash
charmcraft pack
```

### Deploy

```bash
# Create a model
juju add-model indico-dev
# Enable DEBUG logging
juju model-config logging-config="<root>=INFO;unit=DEBUG"
# Deploy the charm
juju deploy ./indico_amd64.charm --resource flask-app-image=localhost:5000/indico:latest
```
