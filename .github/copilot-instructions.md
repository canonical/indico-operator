# Indico Operator - Copilot Instructions

## Overview

Juju Kubernetes Charm for Indico (event management). Python-based using Ops framework.
Main: `src/charm.py`, `src/state.py`, observers for DB/S3/SAML/SMTP.

## Build and Test (CRITICAL)

**Prerequisites**: `pip install tox`. Python 3.12 for plugins, 3.8+ otherwise.

**Pre-commit sequence** (~45-60s total):
```bash
tox -e fmt      # Format with black/isort (2-3s)
tox -e lint     # pydocstyle, codespell, pflake8, isort, black, mypy, pylint (30-50s)
tox -e unit     # Pytest with 97% coverage requirement (7-10s)
tox -e static   # Bandit security scan (4-5s)
```

**After cleanup, use**: `tox -e lint --recreate` (fixes module errors)

**Plugin tests**: `tox -e plugins` (needs Python 3.12 via pyenv)

**Integration tests**: DO NOT run locally - CI only, requires Juju/K8s

## Project Structure

**Root config**: `metadata.yaml` (relations), `config.yaml` (options), `actions.yaml`, `charmcraft.yaml`, `pyproject.toml` (linting), `tox.ini`, `requirements.txt`

**src/**: `charm.py` (main), `state.py` (config), `*_observer.py` (DB/S3/SAML/SMTP relations), `grafana_dashboards/`, `prometheus_alert_rules/`

**tests/**: `unit/` (new), `unit_harness/` (legacy Harness, keep), `integration/` (CI only), `zap/` (security)

**Images**: `indico_rock/rockcraft.yaml` + `plugins/`, `nginx_rock/rockcraft.yaml`

**Docs**: `docs/` (index, tutorial, how-to, reference, explanation, release-notes)

**Other**: `terraform/` (deployment), `load_tests/`, `lib/charms/` (vendored)

## CI Workflows (PR triggers)

**test.yaml**: unit + plugin tests (self-hosted "edge" runner, Python 3.12 for plugins)
**integration_test.yaml**: charm/actions/s3/saml/loki tests, Trivy scan
**docs.yaml**: Vale + Lychee on docs/README
**publish_charm.yaml**: Publishes to edge on main push
**release_notes_automation.yaml**: Generates from `docs/release-notes/artifacts/`

## Known Issues

**Tox cleanup**: After `rm -rf .tox/`, use `tox -e lint --recreate` (fixes module errors)
**WebSockets**: Pinned `<14.0` due to python-libjuju incompatibility
**Harness warnings**: tests/unit_harness/ uses deprecated Harness - keep tests, new tests use tests/unit/ pattern

## Code Style (pyproject.toml)

**Line length**: 99 chars | **Imports**: isort (black profile) | **Docstrings**: Google style | **Types**: mypy required

**Copyright** (flake8-copyright enforced):
```python
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
```

**Coverage**: 97% minimum | **Test files**: `test_*.py` or `*_test.py` | **Docstrings**: src/ required, tests optional

## Making Changes

**Workflow**: `tox -e fmt` → `tox -e lint` → `tox -e unit` → `tox -e static` → commit (CI runs integration)

**Dependencies**: Add to `requirements.txt` (runtime) or `tox.ini` deps (test), check `renovate.json`, verify with `tox -e static`

**Charm logic**: Main in `charm.py`, state in `state.py`, observers for relations. Maintain 97% coverage. Update `metadata.yaml` for relation changes.

**Docs**: Vale (.vale.ini), Lychee (links), woke (.woke.yaml). Check: `make docs-check` (needs vale/lychee installed)

## Key Dependencies

**Runtime**: ops (>=2.0.0,<3.0.0), pydantic (1.10.24)
**Test**: pytest, pytest-asyncio, pytest-operator, juju (2.9.49.0)
**Lint**: black, isort, flake8, mypy, pylint

## Release Notes

Artifacts: `docs/release-notes/artifacts/` | Output: `docs/release-notes/releases/` | Template: `docs/release-notes/template/release-template.md.j2`

## Important Notes

1. **ALWAYS run `tox -e fmt` before `tox -e lint`** - black and isort must format code before linting checks it
2. **DO NOT run integration tests locally** - they require Juju/Kubernetes and are slow
3. **Coverage must stay at 97%+** - add tests for all new code
4. **Python 3.12 is required for plugin tests** - but main code supports Python 3.8+
5. **Use `--recreate` with tox if encountering module errors** after cleaning
6. **Check both unit/ and unit_harness/ directories** - the project has both old and new style tests
7. **Respect the observer pattern** - relations are managed by dedicated observer modules
8. **Follow the Juju charm lifecycle** - install, config-changed, relation events, upgrade
9. **NEVER commit secrets or credentials** - use Juju secrets for sensitive data
10. **Change Artifact Requirement** - A change artifact located in `docs/release-notes/artifacts/pr<PR_NUMBER>.yaml` is **required** for any PR that introduces change. See `release-notes.instructions.md`.
11. **Trust these instructions first** - only search if information is incomplete or appears incorrect
