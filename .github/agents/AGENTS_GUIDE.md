# AI Agents Guide for Indico Operator

This guide explains the GitHub Copilot AI agents available in this repository and how to use them.

## Overview

This repository uses **true GitHub Copilot agents** defined in `.github/agents/*.md` files. These are not GitHub Actions workflows—they are AI-powered agents that you can invoke interactively.

Three specialized agents help maintain release and engineering hygiene:

1. **Drift Detection Agent** (`@drift-detection`) - Finds inconsistencies between code, tests, and docs
2. **Dependency Validator Agent** (`@dependency-validator`) - Assesses risk of dependency updates
3. **Change Artifact Enforcer Agent** (`@change-artifact-enforcer`) - Ensures PRs include release notes

## How to Use Agents

### Invoking Agents

**Via Labels** (most common):
- Add `agent:drift` to trigger drift detection
- Add `agent:dependency-updater` or `renovate` for dependency validation
- `agent:change-artifact` runs automatically on all PRs

**Via @mentions** (interactive):
- Comment `@drift-detection please scan this PR` 
- Comment `@dependency-validator assess this update`
- Comment `@change-artifact-enforcer check compliance`

**Via slash commands**:
- `/scan-drift` - Run drift detection
- `/validate-deps` - Check dependency update
- `/check-artifact` - Verify change artifact

### When Agents Act

- **Drift Detection**: On-demand via label/mention, or manually triggered
- **Dependency Validator**: Automatically on Renovate PRs, or when dependency files change
- **Change Artifact Enforcer**: Automatically on all non-draft PRs

## Agent Descriptions

### Drift Detection Agent

**Purpose**: Identifies gaps between code and tests/documentation

**What it checks**:
- Event handlers without tests
- Config options without documentation
- Actions without how-to guides
- Relations without integration tests

**How to use**:
1. Add label `agent:drift` to any issue or PR
2. Agent scans the repository
3. Posts a structured report with findings and recommendations
4. Review the report and create issues/PRs to address drift

**Example workflow**:
```
1. Add label `agent:drift` to an issue
2. Agent posts report finding 3 missing tests
3. Create tasks to add the missing tests
4. Re-run agent after fixes to verify
```

### Dependency Validator Agent

**Purpose**: Assesses risk and validates dependency updates

**What it checks**:
- Version bump classification (patch/minor/major)
- Security vulnerabilities (pip-audit, CVEs)
- CI test results
- Overall risk level

**How to use**:
1. Renovate creates a dependency update PR
2. Agent automatically runs validation
3. Posts risk assessment with recommendation
4. Agent adds labels: `safe-to-merge` or `needs-review`
5. Review and merge based on assessment

**Risk levels**:
- 🟢 **Low**: Patch bump, no issues, CI passed → Safe to merge
- 🟡 **Medium**: Minor bump, no major issues → Review recommended
- 🟠 **High**: Major bump or concerns → Careful review required
- 🔴 **Critical**: Vulnerabilities or failures → Do not merge

### Change Artifact Enforcer Agent

**Purpose**: Ensures all code changes include release note artifacts

**What it checks**:
- Detects code/config changes in PR
- Validates presence of `docs/release-notes/artifacts/pr<NUMBER>.yaml`
- Validates artifact schema and content
- Provides templates for missing artifacts

**How to use**:
1. Create PR with code changes
2. Agent automatically checks for artifact
3. If missing, agent posts template
4. Create artifact file using template
5. Agent validates and passes check

**Change artifact template**:
```yaml
schema_version: 1
changes:
  - title: "Brief description of your change"
    author: your-github-username
    type: minor  # minor|major|breaking|security|bugfix
    description: |
      Detailed explanation of what changed and why.
      Include user impact and context.
    urls:
      pr: https://github.com/canonical/indico-operator/pull/XXXX
    visibility: public  # public|internal
    highlight: false  # true for significant changes
```

**Exemptions**: Add label `no-changelog` to skip validation for special cases

## Setup and Configuration

### Required Labels

Create these labels in your repository:

```bash
# Agent control labels
gh label create "agent:drift" --description "Trigger drift detection" --color "0E8A16"
gh label create "agent:dependency-updater" --description "Trigger dependency validation" --color "0E8A16"  
gh label create "agent:change-artifact" --description "Trigger artifact validation" --color "0E8A16"

# Status labels
gh label create "renovate" --description "Renovate bot PRs" --color "1E88E5"
gh label create "safe-to-merge" --description "Low risk update" --color "0E8A16"
gh label create "needs-review" --description "Requires review" --color "D93F0B"

# Exemption labels
gh label create "no-changelog" --description "Exempt from changelog" --color "EEEEEE"
gh label create "docs-only" --description "Documentation only" --color "EEEEEE"
gh label create "tests-only" --description "Tests only" --color "EEEEEE"
```

### Branch Protection

Require these checks before merge:
- `unit-tests` - Unit test suite
- `integration-tests` - Integration tests
- `Change Artifact Enforcer` - Artifact validation

Configure in: Settings → Branches → Branch protection rules → `main`

### Python Version

All agents use **Python 3.12** to match repository standards.

## Best Practices

### Working with Drift Detection

- Run drift detection **weekly** to catch issues early
- Address **High** and **Critical** drift items first
- Use drift reports to plan documentation and test improvements
- Re-run after fixes to verify resolution

### Handling Dependency Updates

- Review agent assessments before merging
- For **Low risk** updates: Quick review and merge
- For **Medium risk**: Check changelog and test results
- For **High/Critical**: Detailed review, possibly delay update
- Always test in staging before production

### Managing Change Artifacts

- Create artifacts **early** in PR lifecycle
- Be specific in titles and descriptions
- Use correct `type` classification
- Set `highlight: true` only for major features
- Link related issues in `urls.related_issue`

## Troubleshooting

### Agent Not Responding

1. Check label spelling (case-sensitive)
2. Verify agent is mentioned correctly with `@`
3. Ensure you have required permissions
4. Check GitHub Actions logs for errors

### False Positives in Drift Detection

If agent reports drift incorrectly:
- Add exemption patterns to agent configuration
- Report false positive for agent improvement
- Use manual review to override

### Artifact Validation Failures

Common issues:
- **Wrong file location**: Must be in `docs/release-notes/artifacts/`
- **Invalid YAML**: Check syntax with yamllint
- **Schema errors**: Verify all required fields present
- **Field validation**: Check min/max lengths, valid enums

## Support

- **Agent definitions**: See `.github/agents/*.md` for agent specifications
- **Issues**: Report agent problems with label `automation`
- **Questions**: Ask in PR comments or repository discussions

## Architecture Notes

These are **GitHub Copilot agents**, not GitHub Actions workflows:

- **Agent definitions** live in `.github/agents/*.md` files
- Agents are invoked via labels, @mentions, or slash commands
- Agents use AI to interpret their directives and take action
- No hard-coded workflows—behavior is defined in the .md files
- Agents can be iteratively improved by editing their definitions

This differs from traditional CI/CD automation where logic is hard-coded in YAML workflows. Agents are more flexible and can adapt their behavior based on context.

## Version

- **Agent System Version**: 1.0.0
- **GitHub Copilot Agents**: Enabled
- **Python**: 3.12
- **Last Updated**: 2025-11-06
