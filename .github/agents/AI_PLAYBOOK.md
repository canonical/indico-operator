# AI Playbook for Indico Operator

## Overview

This playbook defines the governance, best practices, and operational guidelines for AI-powered automation agents in the Indico Operator repository. These agents are designed to improve reliability, velocity, and consistency in our development and release workflows.

## Core Principles

### 1. Human-in-the-Loop
- **All agents work via Pull Requests**: Never push directly to protected branches
- **Changes require human review**: All PRs must be reviewed and approved by maintainers
- **Clear communication**: Agents provide human-readable summaries and next steps
- **Transparent operations**: All agent actions are logged and auditable

### 2. Label-Gated Operations
Agents are triggered and controlled via GitHub labels:
- `agent:drift` - Triggers drift detection and resolution
- `agent:dependency-updater` - Activates dependency update validation
- `agent:change-artifact` - Enforces change artifact requirements
- `renovate` - Identifies Renovate-created PRs for dependency tracking
- `automation` - General automation marker
- `release-notes` - Release notes related changes
- `docs` - Documentation changes

### 3. Quality Gates
All agent-created PRs must pass:
- **Linting**: Code style and quality checks (tox -e lint)
- **Unit Tests**: All unit tests must pass (tox -e unit)
- **Integration Tests**: Where applicable
- **Packaging**: Charm packaging validation (charmcraft pack)
- **Security**: CodeQL and vulnerability scanning

### 4. Release Management
- **Change artifacts required**: All code/config changes must include `docs/release-notes/artifacts/pr<PR_NUMBER>.yaml`
- **Release notes automation**: Release notes are generated from change and release artifacts
- **Human oversight**: All releases require manual approval and review

## Agent Definitions

### 1. Drift Agent

**Purpose**: Detect and resolve drift between code, tests, documentation, and configuration.

**Scope**:
- Charm event handlers and relations vs. test coverage
- Configuration (config.yaml, actions.yaml) vs. documentation
- Code implementations vs. runbooks and guides

**Triggers**:
- Label: `agent:drift`
- Can be run on-demand or periodically (scheduled)
- Can operate in dry-run mode (report only) or active mode (create PRs)

**Behaviors**:
- Analyzes charm.py for event handlers and relation observers
- Checks test files for corresponding test coverage
- Validates config.yaml and actions.yaml against documentation
- Identifies missing or outdated documentation
- Creates PRs with suggested fixes or reports findings as issues

**Outputs**:
- Drift detection report (as PR comment or issue)
- Pull requests with test additions or documentation updates
- Summary of actions taken and recommendations

### 2. Dependency Update Agent

**Purpose**: Automate and validate dependency updates in collaboration with Renovate.

**Scope**:
- Python dependencies (requirements.txt, pyproject.toml)
- Charm library updates
- Base image updates (rockcraft files)
- Terraform provider updates

**Triggers**:
- Label: `renovate` (automatically on Renovate PRs)
- Label: `agent:dependency-updater`
- Automatically monitors Renovate PRs

**Behaviors**:
- Validates Renovate PRs pass all CI checks
- Runs security vulnerability scanning on new dependencies
- Adds risk assessment comment to PR
- Includes upstream changelog summary
- Proposes targeted minor/patch bumps (never major without explicit label)
- Rolls back if CI fails

**Outputs**:
- Risk assessment comment on Renovate PRs
- Upstream changelog summary
- CI status validation
- Approval recommendation or concerns raised

### 3. Change Artifact Enforcement Agent

**Purpose**: Ensure all code changes include structured change artifacts for release notes.

**Scope**:
- All PRs touching charm code (src/, lib/)
- All PRs modifying configuration (config.yaml, actions.yaml, metadata.yaml)
- All PRs changing container images or dependencies

**Triggers**:
- Automatically on all pull requests
- Label: `agent:change-artifact`

**Behaviors**:
- Detects code/config changes in PR
- Validates presence of `docs/release-notes/artifacts/pr<PR_NUMBER>.yaml`
- Fails CI check if artifact missing for code changes
- Provides template for creating change artifact
- Exempts documentation-only changes (unless specifically marked)

**Outputs**:
- CI check status (pass/fail)
- Comment with change artifact template if missing
- Guidance on completing the artifact
- Links to documentation and examples

## Operational Guidelines

### Running Agents

#### Manual Trigger
Apply the appropriate label to a PR or issue:
```bash
# Trigger drift agent
gh pr edit <PR_NUMBER> --add-label "agent:drift"

# Trigger dependency updater
gh pr edit <PR_NUMBER> --add-label "agent:dependency-updater"

# Change artifact is automatic but can be re-triggered
gh pr edit <PR_NUMBER> --add-label "agent:change-artifact"
```

#### Scheduled Runs
- **Drift Agent**: Weekly scan on main branch (Sunday 00:00 UTC)
- **Dependency Updates**: Monitored continuously via Renovate integration
- **Change Artifacts**: Validated on every PR

### Agent Permissions

Agents operate with limited permissions:
- **Read**: Full repository access
- **Write**: Can create branches, PRs, and comments
- **No direct push**: Cannot push to protected branches
- **No merge**: Cannot merge PRs (requires human approval)

### Security Considerations

1. **Secret Handling**: Agents never access or expose secrets
2. **Code Execution**: All code changes are validated through CI
3. **Dependency Validation**: All new dependencies are scanned for vulnerabilities
4. **Audit Trail**: All agent actions are logged and traceable
5. **Rate Limiting**: Agents respect GitHub API rate limits

## Python Version Support

- **Primary Python Version**: 3.12
- All CI runs use Python 3.12
- Agents validate compatibility with Python 3.12
- Future support for other versions requires explicit configuration

## Branch Protection

The following checks are required before merging:

### Required Checks
- `unit-tests` - Unit test suite
- `plugins-test` - Plugin-specific tests  
- `integration-tests` - Full integration test suite
- `docs-checks` - Documentation validation
- `change-artifact-check` - Change artifact validation
- `terraform-validate` - Terraform configuration validation (if applicable)

### Protected Branches
- `main` - Primary development branch
- `track/*` - Release track branches

All protected branches require:
- At least one approval from a maintainer
- All required checks passing
- No unresolved conversations
- Branch must be up to date with base branch

## Troubleshooting

### Agent Not Triggering
1. Verify label is correctly applied
2. Check workflow runs in Actions tab
3. Verify agent workflows are enabled
4. Check for workflow syntax errors

### Agent Created Invalid PR
1. Close the PR with explanation
2. Report issue with agent behavior
3. Adjust agent configuration as needed
4. Re-trigger with corrections

### CI Failures on Agent PRs
1. Review failure logs
2. Determine if issue is with agent changes or existing code
3. Fix issues manually or request agent re-run
4. Update agent logic if systematic issue found

## Future Enhancements

Potential future agents:
- **Test Coverage Agent**: Automatically maintain test coverage thresholds
- **Documentation Sync Agent**: Keep docs in sync with code changes
- **Performance Regression Agent**: Detect performance regressions
- **Security Audit Agent**: Automated security audits and compliance checks

## References

- [Release Notes Automation](https://github.com/canonical/release-notes-automation)
- [Charm Style Guide](https://juju.is/docs/sdk/styleguide)
- [Contributing Guide](https://github.com/canonical/is-charms-contributing-guide)
- [ISD054 - Managing Charm Complexity](https://discourse.charmhub.io/t/specification-isd014-managing-charm-complexity/11619)

## Support

For issues, questions, or suggestions regarding AI agents:
- Open an issue with label `automation`
- Tag `@copilot` for agent-specific issues
- Consult this playbook for operational guidance
