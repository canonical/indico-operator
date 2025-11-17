# Indico Operator - Copilot Instructions

## Repository Overview

This repository contains the Indico Operator, a Juju charm for deploying and managing Indico (an open-source event organization and collaboration tool) on Kubernetes. The charm is written in Python and uses the Ops framework.

**Key Facts:**
- **Type**: Juju Kubernetes Charm (Python-based)
- **Size**: ~1,400 lines of source code, ~2,400 lines of test code
- **Languages**: Python 3.12 (required for some tests), Python 3.8+ supported for main code
- **Frameworks**: Juju Ops framework, pytest for testing
- **Build Tools**: tox, charmcraft, rockcraft
- **Main Files**: `src/charm.py` (987 lines), `src/state.py` (238 lines), plus observer modules

## Build and Test Commands

### Prerequisites

**ALWAYS install tox first:**
```bash
pip install tox
```

**Python Version Requirements:**
- Main code and most tests: Python 3.8+ (default Python 3.12.3 works)
- Plugin tests (`tox -e plugins`): Requires Python 3.12, installed via pyenv (see tests/unit_harness/pre_run_script.sh)

### Linting (ALWAYS run before committing)

```bash
tox -e lint
```

**Time**: ~30-50 seconds (first run), ~10-15 seconds (cached)

This runs:
1. `pydocstyle` - docstring style checking
2. `codespell` - spell checking
3. `pflake8` - flake8 with pyproject.toml support
4. `isort --check-only --diff` - import sorting verification
5. `black --check --diff` - code formatting verification
6. `mypy` - type checking
7. `pylint` - comprehensive linting

**IMPORTANT**: If lint fails after cleanup, use `--recreate`:
```bash
rm -rf .tox/
tox -e lint --recreate
```

### Formatting Code

```bash
tox -e fmt
```

**Time**: ~2-3 seconds

This applies:
- `isort` - sorts imports
- `black` - formats code to consistent style

### Unit Tests

```bash
tox -e unit
```

**Time**: ~7-10 seconds

Runs pytest on tests/unit/ and tests/unit_harness/ directories with coverage reporting. **Coverage requirement: 97%** - your changes must maintain or improve coverage.

### Static Analysis (Security)

```bash
tox -e static
```

**Time**: ~4-5 seconds

Runs `bandit` security linter to detect security issues.

### Plugin Tests

```bash
tox -e plugins
```

**Time**: ~30-60 seconds

Tests Indico plugins in indico_rock/plugins/. Requires Python 3.12 installed via pyenv.

### Integration Tests

Integration tests run in CI via GitHub Actions and require a full Juju environment. They are defined in `tests/integration/` and test:
- test_charm.py - Basic charm functionality
- test_actions.py - Charm actions
- test_s3.py - S3 integration
- test_saml.py - SAML authentication
- test_loki.py - Logging integration

**DO NOT run integration tests locally** - they require Kubernetes and Juju setup.

### Full Test Sequence (Recommended Before Committing)

```bash
# Format code first
tox -e fmt

# Run all local checks
tox -e lint
tox -e unit
tox -e static
```

**Total time**: ~45-60 seconds

## Project Structure

### Source Code (`src/`)
- **`charm.py`** - Main charm logic (987 lines), implements IndicoOperatorCharm
- **`state.py`** - Configuration and state management (238 lines)
- **`database_observer.py`** - PostgreSQL database relation observer
- **`s3_observer.py`** - S3 storage relation observer
- **`saml_observer.py`** - SAML authentication relation observer
- **`smtp_observer.py`** - SMTP email relation observer
- **`grafana_dashboards/`** - Grafana dashboard definitions
- **`prometheus_alert_rules/`** - Prometheus alerting rules

### Tests (`tests/`)
- **`unit/`** - New-style unit tests (ops testing framework)
- **`unit_harness/`** - Legacy unit tests using Harness (deprecated but functional)
- **`integration/`** - Integration tests (require Juju environment, run in CI only)
- **`zap/`** - ZAP security testing hooks
- **`conftest.py`** - Shared pytest fixtures

### Configuration Files (Root)
- **`metadata.yaml`** - Charm metadata (relations, containers, resources)
- **`config.yaml`** - Charm configuration options
- **`actions.yaml`** - Charm actions (refresh-external-resources, add-admin, anonymize-user)
- **`charmcraft.yaml`** - Charmcraft build configuration
- **`pyproject.toml`** - Python project config (black, flake8, isort, mypy, pylint settings)
- **`tox.ini`** - Tox test environments
- **`requirements.txt`** - Runtime dependencies (pydantic, ops)
- **`renovate.json`** - Renovate bot dependency update configuration

### OCI Images (`indico_rock/`, `nginx_rock/`)
- **`indico_rock/rockcraft.yaml`** - Indico container image definition
- **`indico_rock/plugins/`** - Custom Indico plugins (autocreate, anonymize)
- **`nginx_rock/rockcraft.yaml`** - Nginx container image definition

### Documentation (`docs/`)
- **`index.md`** - Main documentation index
- **`tutorial.md`** - Getting started tutorial
- **`how-to/`** - How-to guides
- **`reference/`** - Reference documentation
- **`explanation/`** - Explanatory documentation
- **`release-notes/`** - Release notes and artifacts

### Other
- **`terraform/`** - Terraform module for deploying the charm
- **`load_tests/`** - Load testing scripts
- **`lib/charms/`** - Charm libraries (vendored dependencies)

## GitHub Actions CI/CD

### Main Workflows

**`.github/workflows/test.yaml`** (On every PR)
- Runs `tox -e unit` via canonical/operator-workflows
- Runs plugin tests on Ubuntu 22.04 with Python 3.12

**`.github/workflows/integration_test.yaml`** (On every PR)
- Runs integration tests via canonical/operator-workflows
- Tests: test_charm.py, test_actions.py, test_s3.py, test_saml.py, test_loki.py
- Includes Trivy security scanning
- ZAP security scanning (currently disabled)

**`.github/workflows/docs.yaml`** (On PR and main push)
- Runs Vale prose linting on docs/ and README.md
- Runs Lychee link checking

**`.github/workflows/publish_charm.yaml`** (On main/track/* push)
- Publishes charm to edge channel via canonical/operator-workflows

**`.github/workflows/promote_charm.yaml`** (Manual)
- Promotes charm between channels

**`.github/workflows/release_notes_automation.yaml`** (On release notes changes)
- Generates release notes from artifacts

### Important CI Details

1. **Self-hosted runners**: Unit tests use self-hosted runners with label "edge"
2. **Python 3.12 requirement**: Plugin tests require Python 3.12 installed via pyenv
3. **Workflow reuse**: Most workflows reuse canonical/operator-workflows templates
4. **Trivy scanning**: Enabled for container images (config: trivy.yaml)

## Common Issues and Workarounds

### Issue: Tox environment corruption after cleanup

**Problem**: After running `rm -rf .tox/`, running `tox -e lint` may fail with "ModuleNotFoundError: No module named 'pip._internal.cli.main_parser'"

**Solution**: Use `--recreate` flag:
```bash
rm -rf .tox/
tox -e lint --recreate
```

### Issue: WebSockets compatibility

**Problem**: There is a known incompatibility with websockets lib >= 14.0 and python-libjuju.

**Solution**: Already pinned in tox.ini:
```ini
websockets<14.0 # https://github.com/juju/python-libjuju/issues/1184
```

### Issue: Harness deprecation warnings

**Problem**: Unit tests using Harness show deprecation warnings.

**Context**: Legacy tests in tests/unit_harness/ use deprecated Harness. New tests should use the ops testing framework (see tests/unit/).

**Action**: For new tests, follow patterns in tests/unit/. Do NOT remove existing Harness tests - they are functional and provide coverage.

## Code Style and Standards

### Style Configuration
- **Line length**: 99 characters (black, flake8)
- **Import sorting**: isort with black profile
- **Docstring style**: Google style
- **Type hints**: Required and checked by mypy

### Copyright Headers
ALL Python files must start with:
```python
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
```

This is enforced by flake8-copyright.

### Testing Standards
- **Coverage requirement**: 97% (enforced in pyproject.toml)
- **Test naming**: `test_*.py` or `*_test.py`
- **Docstrings**: Required for all public functions in src/, optional for tests

## Making Changes

### Workflow for Code Changes

1. **Format code**:
   ```bash
   tox -e fmt
   ```

2. **Run linting**:
   ```bash
   tox -e lint
   ```

3. **Run unit tests**:
   ```bash
   tox -e unit
   ```

4. **Run security scan**:
   ```bash
   tox -e static
   ```

5. **Commit changes** (CI will run integration tests automatically)

### When Adding Dependencies

- Add to `requirements.txt` for runtime dependencies
- Add to tox.ini `[testenv:*]` deps for test dependencies
- Check `renovate.json` for automatic updates configuration
- Verify with security scan: `tox -e static`

### When Modifying Charm Logic

- Main charm logic is in `src/charm.py`
- State management is in `src/state.py`
- Observer pattern is used for relations (database_observer.py, s3_observer.py, etc.)
- Always maintain 97% test coverage
- Update metadata.yaml if changing relations/resources

### Documentation Changes

Documentation uses:
- **Vale** for prose linting (config: .vale.ini, styles in .vale/)
- **Lychee** for link checking
- **woke** for inclusive language checking (config: .woke.yaml)

To check docs locally (requires vale and lychee installed):
```bash
make docs-check
```

## Key Dependencies

- **ops** (>=2.0.0,<3.0.0) - Juju operator framework
- **pydantic** (1.10.24) - Data validation
- **juju** (2.9.49.0 for integration tests) - Juju client library
- **pytest**, **pytest-asyncio**, **pytest-operator** - Testing framework
- **black**, **isort**, **flake8**, **mypy**, **pylint** - Code quality tools

## Release Notes

The repository uses release-notes-automation workflow:
- Change artifacts go in `docs/release-notes/artifacts/`
- Releases are generated in `docs/release-notes/releases/`
- Template is at `docs/release-notes/template/release-template.md.j2`

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
10. **Trust these instructions first** - only search if information is incomplete or appears incorrect
