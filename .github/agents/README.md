# AI Automation Agents

This directory contains definitions, documentation, and governance for AI-powered automation agents used in the Indico Operator repository.

## Overview

AI automation agents help streamline development workflows, enforce best practices, and maintain consistency across code, tests, and documentation. These agents operate through GitHub Actions workflows and are designed to augment (not replace) human decision-making.

## Available Agents

### 1. 🔍 Drift Detection Agent
**Purpose**: Detect and resolve drift between code, tests, documentation, and configuration.

**Triggers**: 
- Label: `agent:drift`
- Scheduled: Weekly (Sunday 00:00 UTC)
- Manual: Workflow dispatch

**What it does**:
- Identifies missing tests for event handlers and relations
- Flags undocumented configuration options and actions
- Detects missing or outdated documentation
- Creates reports or PRs with suggested fixes

**Learn more**: [drift-agent.md](drift-agent.md)

### 2. 📦 Dependency Update Agent
**Purpose**: Automate validation and risk assessment of dependency updates.

**Triggers**:
- Automatically on Renovate PRs
- Label: `agent:dependency-updater`
- Label: `renovate` or `dependencies`

**What it does**:
- Validates Renovate PRs pass all CI checks
- Runs security vulnerability scanning
- Provides risk assessment and recommendations
- Auto-approves safe updates (patch versions)
- Requests review for risky updates

**Learn more**: [dependency-update-agent.md](dependency-update-agent.md)

### 3. 📝 Change Artifact Enforcement Agent
**Purpose**: Ensure all code changes include structured change artifacts for release notes.

**Triggers**:
- Automatically on all pull requests
- Validates on PR open/update

**What it does**:
- Detects code/config changes requiring artifacts
- Validates change artifact presence and schema
- Provides templates for missing artifacts
- Fails CI if artifact missing for code changes
- Exempts documentation-only changes

**Learn more**: [change-artifact-agent.md](change-artifact-agent.md)

## Quick Start

### For Contributors

1. **Making a code change?**
   - Your PR will automatically be checked for a change artifact
   - If required, create `docs/release-notes/artifacts/pr<NUMBER>.yaml`
   - Use the template provided in the automated comment
   - See [_change-artifact-template.yaml](../docs/release-notes/template/_change-artifact-template.yaml)

2. **Want to check for drift?**
   - Add label `agent:drift` to an issue or PR
   - Agent will scan and post a report
   - Review findings and create issues/PRs to address them

3. **Reviewing a dependency update?**
   - Agent automatically assesses Renovate PRs
   - Check the risk assessment comment
   - Follow the recommendation (approve, review, or block)

### For Maintainers

1. **Set up required labels**: See [LABELS_AND_CONFIG.md](LABELS_AND_CONFIG.md)
2. **Configure branch protection**: Enable required status checks
3. **Review agent reports**: Monitor agent-created issues and comments
4. **Adjust as needed**: Update agent configurations based on team feedback

## Agent Principles

All agents follow these core principles:

1. **Human-in-the-Loop**: All agents work via PRs that require human review and approval
2. **Label-Gated**: Agents are triggered and controlled via GitHub labels
3. **Quality Gates**: All PRs must pass linting, tests, and packaging checks
4. **Transparent**: All agent actions are logged and auditable
5. **Safe**: Agents never push directly to protected branches

## Documentation

- **[AI_PLAYBOOK.md](AI_PLAYBOOK.md)**: Complete governance and operational guidelines
- **[LABELS_AND_CONFIG.md](LABELS_AND_CONFIG.md)**: Label definitions and configuration
- **[drift-agent.md](drift-agent.md)**: Drift Detection Agent specification
- **[dependency-update-agent.md](dependency-update-agent.md)**: Dependency Update Agent specification
- **[change-artifact-agent.md](change-artifact-agent.md)**: Change Artifact Agent specification

## Workflows

The agent workflows are located in `.github/workflows/`:

- `change_artifact_check.yaml` - Change Artifact Enforcement
- `drift_detection.yaml` - Drift Detection
- `dependency_update_validation.yaml` - Dependency Update Validation

## Usage Examples

### Trigger Drift Detection

```bash
# On an existing issue or PR
gh issue edit <ISSUE_NUMBER> --add-label "agent:drift"

# Or create a new issue
gh issue create --title "Drift Detection Scan" --label "agent:drift" --body "Requesting drift detection scan"

# Or use workflow dispatch
gh workflow run drift_detection.yaml -f mode=report
```

### Review Dependency Updates

Renovate PRs are automatically assessed. To manually trigger:

```bash
gh pr edit <PR_NUMBER> --add-label "agent:dependency-updater"
```

### Validate Change Artifact

Automatic on all PRs. To manually re-check:

```bash
# Comment on the PR
gh pr comment <PR_NUMBER> --body "check-artifact"

# Or add the label
gh pr edit <PR_NUMBER> --add-label "agent:change-artifact"
```

## Monitoring and Metrics

### Check Agent Status

```bash
# View recent workflow runs
gh run list --workflow=drift_detection.yaml --limit 5
gh run list --workflow=change_artifact_check.yaml --limit 5
gh run list --workflow=dependency_update_validation.yaml --limit 5

# View specific run details
gh run view <RUN_ID>
```

### Agent Metrics

Agents track these metrics:
- **Drift Detection**: Items found, false positives, resolution time
- **Dependency Updates**: Auto-approval rate, false positives, rollback rate
- **Change Artifacts**: Compliance rate, validation errors, time to add

## Troubleshooting

### Agent Not Running

1. Check if label is correctly applied
2. Verify workflow is enabled in repository settings
3. Check workflow run logs in Actions tab
4. Ensure trigger conditions are met

### False Positives

1. Review agent detection rules
2. Add exemptions if appropriate
3. Update agent configuration
4. Report issue for agent improvement

### Workflow Failures

1. Check workflow logs for errors
2. Verify required permissions are granted
3. Ensure dependencies are available
4. Report persistent issues

## Contributing to Agents

### Improving Agent Logic

1. Review agent definition files
2. Propose changes via PR
3. Update documentation
4. Test with sample data
5. Monitor after deployment

### Adding New Agents

1. Create agent definition document
2. Implement workflow
3. Add to this README
4. Update AI_PLAYBOOK.md
5. Test thoroughly
6. Document usage

## Python Version

All agents use **Python 3.12** as specified in the repository requirements. This ensures consistency across CI/CD and local development.

## Support

For issues, questions, or suggestions:

1. **General questions**: Open a discussion
2. **Bug reports**: Create an issue with label `automation`
3. **Feature requests**: Create an issue describing the enhancement
4. **Urgent issues**: Tag `@copilot` in the issue

## References

- [Release Notes Automation](https://github.com/canonical/release-notes-automation)
- [Charm Style Guide](https://juju.is/docs/sdk/styleguide)
- [Contributing Guide](https://github.com/canonical/is-charms-contributing-guide)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Version History

- **v1.0.0** (2025): Initial implementation of three core agents
  - Drift Detection Agent
  - Dependency Update Agent
  - Change Artifact Enforcement Agent

## License

These agents are part of the Indico Operator repository and are licensed under the same terms. See [LICENSE](../../LICENSE) for details.
