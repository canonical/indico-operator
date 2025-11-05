# AI Agents - Labels and Configuration

## Required GitHub Labels

The following labels should be created in the repository to support AI agent operations:

### Agent Control Labels

| Label | Color | Description | Used By |
|-------|-------|-------------|---------|
| `agent:drift` | `#0E8A16` | Triggers drift detection and resolution | Drift Agent |
| `agent:dependency-updater` | `#0E8A16` | Triggers dependency update validation | Dependency Update Agent |
| `agent:change-artifact` | `#0E8A16` | Triggers change artifact validation (automatic) | Change Artifact Agent |

### Dependency Management Labels

| Label | Color | Description | Used By |
|-------|-------|-------------|---------|
| `renovate` | `#1E88E5` | PRs created by Renovate bot | Dependency Update Agent, Renovate |
| `dependencies` | `#0366D6` | Dependency update PRs | Dependency Update Agent |
| `safe-to-merge` | `#0E8A16` | Low risk updates safe to merge | Dependency Update Agent |
| `needs-review` | `#D93F0B` | High risk updates needing review | Dependency Update Agent |

### Release Management Labels

| Label | Color | Description | Used By |
|-------|-------|-------------|---------|
| `release-notes` | `#0075CA` | Release notes related changes | Release automation |
| `no-changelog` | `#EEEEEE` | Changes exempt from changelog | Change Artifact Agent |

### General Labels

| Label | Color | Description | Used By |
|-------|-------|-------------|---------|
| `automation` | `#5319E7` | Automation-related issues/PRs | All agents |
| `docs` | `#0075CA` | Documentation changes | Drift Agent |
| `docs-only` | `#EEEEEE` | Documentation-only changes (exempt) | Change Artifact Agent |
| `tests-only` | `#EEEEEE` | Test-only changes (exempt) | Change Artifact Agent |
| `maintenance` | `#FBCA04` | Maintenance tasks (exempt) | Change Artifact Agent |
| `drift-detection` | `#FEF2C0` | Drift detection reports | Drift Agent |

## Creating Labels

### Using GitHub CLI

```bash
# Agent control labels
gh label create "agent:drift" --description "Trigger drift detection agent" --color "0E8A16"
gh label create "agent:dependency-updater" --description "Trigger dependency update agent" --color "0E8A16"
gh label create "agent:change-artifact" --description "Trigger change artifact validation" --color "0E8A16"

# Dependency labels
gh label create "renovate" --description "Renovate bot PRs" --color "1E88E5"
gh label create "dependencies" --description "Dependency updates" --color "0366D6"
gh label create "safe-to-merge" --description "Low risk, safe to merge" --color "0E8A16"
gh label create "needs-review" --description "Requires manual review" --color "D93F0B"

# Release labels
gh label create "release-notes" --description "Release notes related" --color "0075CA"
gh label create "no-changelog" --description "Exempt from changelog" --color "EEEEEE"

# General labels
gh label create "automation" --description "Automation related" --color "5319E7"
gh label create "docs" --description "Documentation changes" --color "0075CA"
gh label create "docs-only" --description "Documentation only" --color "EEEEEE"
gh label create "tests-only" --description "Test changes only" --color "EEEEEE"
gh label create "maintenance" --description "Maintenance tasks" --color "FBCA04"
gh label create "drift-detection" --description "Drift detection report" --color "FEF2C0"
```

### Using GitHub Web UI

1. Navigate to `https://github.com/canonical/indico-operator/labels`
2. Click "New label"
3. Enter label name, description, and color
4. Click "Create label"
5. Repeat for all labels above

## Branch Protection Rules

### Protected Branches

#### `main` branch

**Required status checks:**
- `unit-tests` - Unit test suite
- `plugins-test` - Plugin-specific tests
- `integration-tests` - Integration test suite (when applicable)
- `docs-checks` - Documentation validation
- `change-artifact-check` - Change artifact validation
- `terraform-validate` - Terraform validation (when applicable)

**Branch protection settings:**
```yaml
required_status_checks:
  strict: true
  checks:
    - unit-tests
    - plugins-test
    - integration-tests
    - docs-checks
    - Validate Change Artifact  # From change_artifact_check workflow

required_pull_request_reviews:
  required_approving_review_count: 1
  dismiss_stale_reviews: true
  require_code_owner_reviews: true

enforce_admins: false

restrictions: null

required_linear_history: false

allow_force_pushes: false

allow_deletions: false
```

#### `track/*` branches

Same rules as `main` branch.

### Configuring Branch Protection

#### Using GitHub CLI

```bash
# Enable branch protection for main
gh api repos/canonical/indico-operator/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"checks":[{"context":"unit-tests"},{"context":"plugins-test"},{"context":"Validate Change Artifact"}]}' \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field enforce_admins=false \
  --field restrictions=null
```

#### Using GitHub Web UI

1. Go to `Settings` → `Branches`
2. Click "Add rule" or edit existing rule for `main`
3. Configure:
   - ☑ Require a pull request before merging
     - ☑ Require approvals (1)
     - ☑ Dismiss stale pull request approvals when new commits are pushed
   - ☑ Require status checks to pass before merging
     - ☑ Require branches to be up to date before merging
     - Select required checks:
       - unit-tests
       - plugins-test
       - Validate Change Artifact
   - ☑ Require conversation resolution before merging
4. Save changes

## Agent Workflow Permissions

Each agent workflow requires specific permissions:

### Change Artifact Enforcement
```yaml
permissions:
  contents: read
  pull-requests: write
  checks: write
```

### Drift Detection
```yaml
permissions:
  contents: write
  issues: write
  pull-requests: write
```

### Dependency Update Validation
```yaml
permissions:
  contents: read
  pull-requests: write
  checks: write
```

## Environment Variables and Secrets

### Required Secrets

No additional secrets are required beyond the default `GITHUB_TOKEN` which is automatically provided by GitHub Actions.

### Optional Configuration

If needed, these can be configured as repository variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DRIFT_SCAN_SCHEDULE` | Cron schedule for drift scans | `0 0 * * 0` (Weekly) |
| `DEPENDENCY_MAX_WAIT` | Max wait time for CI (seconds) | `1800` (30 min) |
| `ARTIFACT_EXEMPT_LABELS` | Additional exempt labels | (see workflow) |

## Troubleshooting

### Labels Not Working

**Issue**: Agent not triggered when label applied

**Solutions**:
1. Verify label name matches exactly (case-sensitive)
2. Check workflow file has correct trigger configuration
3. Verify workflows are enabled in repository settings
4. Check Actions tab for workflow run errors

### Branch Protection Blocking PRs

**Issue**: Required checks not passing

**Solutions**:
1. Verify check names match exactly in branch protection
2. Check if workflows are running on PR
3. Review workflow logs for errors
4. Ensure all required files are present (e.g., change artifact)

### Permissions Errors

**Issue**: Agent cannot comment or update status

**Solutions**:
1. Verify workflow permissions are correctly set
2. Check repository settings allow workflows to create PRs/comments
3. Verify GITHUB_TOKEN has required scopes

## Additional Resources

- [GitHub Labels Documentation](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/managing-labels)
- [Branch Protection Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub Actions Permissions](https://docs.github.com/en/actions/security-guides/automatic-token-authentication#permissions-for-the-github_token)
