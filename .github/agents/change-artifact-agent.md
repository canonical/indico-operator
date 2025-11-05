# Change Artifact Enforcement Agent Definition

## Agent Identity

- **Name**: Change Artifact Enforcement Agent
- **Label**: `agent:change-artifact`
- **Version**: 1.0.0
- **Owner**: Platform Engineering Team

## Purpose

Ensure every code and configuration change includes a structured change artifact (YAML) that will be used for automated release notes generation. This agent enforces release hygiene and ensures no changes are lost in release documentation.

## Scope

### In Scope - Changes Requiring Artifacts

1. **Charm Code Changes**
   - src/*.py modifications
   - lib/charms/* library changes
   - New event handlers or observers

2. **Configuration Changes**
   - config.yaml modifications
   - actions.yaml changes
   - metadata.yaml updates
   - charmcraft.yaml changes

3. **Container/Image Changes**
   - rockcraft.yaml modifications
   - OCI image version updates
   - Base image changes

4. **Dependency Changes**
   - requirements.txt updates
   - pyproject.toml dependency changes
   - Significant library version updates

5. **Workflow/CI Changes**
   - .github/workflows/* changes (if they affect behavior)
   - tox.ini configuration updates
   - Makefile changes affecting builds

### Out of Scope - Exempt from Artifacts

1. **Documentation-Only Changes**
   - docs/* modifications (unless changing documented behavior)
   - README.md updates
   - Comment-only changes

2. **Test-Only Changes**
   - tests/* additions/modifications (unless fixing prod bugs)
   - Test data or fixtures
   - Conftest updates

3. **Maintenance Tasks**
   - .gitignore updates
   - .editorconfig changes
   - Code formatting (black, isort)
   - Dependency updates with no functional impact

4. **Automation Updates**
   - Renovate configuration
   - Dependabot configuration
   - GitHub Actions dependency updates

## Validation Rules

### Rule 1: Artifact File Presence
**Condition**: PR contains in-scope changes
**Expected**: File exists at `docs/release-notes/artifacts/pr<PR_NUMBER>.yaml`
**Action**: Fail CI check if missing, provide template in comment

### Rule 2: Artifact Schema Validation
**Condition**: Artifact file exists
**Expected**: Valid schema_version: 1 format
**Required Fields**:
- `schema_version`: Must be 1
- `changes`: Array with at least one change entry
- `changes[].title`: Non-empty string
- `changes[].author`: GitHub username
- `changes[].type`: One of [minor, major, breaking, security, bugfix]
- `changes[].description`: Detailed description
- `changes[].urls.pr`: PR URL
- `changes[].visibility`: public or internal
- `changes[].highlight`: boolean

**Action**: Fail CI if schema invalid, provide corrected template

### Rule 3: Content Quality Check
**Condition**: Artifact passes schema validation
**Expected**: 
- Title is descriptive (min 10 chars)
- Description provides context (min 20 chars)
- Type matches change nature
- PR URL is correct

**Action**: Warn if quality issues detected, suggest improvements

### Rule 4: Multiple Changes Support
**Condition**: PR contains multiple logical changes
**Expected**: Multiple entries in changes array
**Action**: Suggest breaking into separate entries

### Rule 5: Exemption Markers
**Condition**: PR labeled with exemption label
**Allowed Labels**: `no-changelog`, `docs-only`, `tests-only`, `maintenance`
**Action**: Skip artifact validation

## Operation Modes

### 1. Automatic Validation (Default)
- **Trigger**: Automatically on all pull requests
- **Behavior**:
  - Detects in-scope file changes
  - Validates artifact presence and schema
  - Updates check status (pass/fail)
  - Comments with guidance if failing

### 2. Template Generation
- **Trigger**: PR missing artifact file
- **Behavior**:
  - Generates pre-filled template with PR metadata
  - Posts as PR comment
  - Links to documentation
  - Provides examples

### 3. Manual Re-check
- **Trigger**: Label `agent:change-artifact` or comment "check-artifact"
- **Behavior**:
  - Re-runs validation
  - Updates check status
  - Useful after artifact is added

## Workflow

### Trigger Conditions
1. **Automatic**: All pull requests on open/synchronize
2. **Manual**: Comment "check-artifact" on PR
3. **Re-check**: After artifact file is added to PR

### Execution Steps

#### Phase 1: Change Detection
1. **Get PR Files**: Fetch list of changed files from PR
2. **Classify Changes**: Determine if in-scope or exempt
3. **Calculate Scope**: Determine if artifact required

#### Phase 2: Artifact Validation
1. **Check File Exists**: Look for pr<NUMBER>.yaml in artifacts directory
2. **Parse YAML**: Load and validate YAML structure
3. **Schema Check**: Validate against required schema
4. **Content Check**: Verify field values and quality

#### Phase 3: Status Update
1. **Set Check Status**: Pass/fail/warning
2. **Generate Message**: Create detailed status message
3. **Post Comment**: Add guidance comment if needed
4. **Update Labels**: Add appropriate labels

#### Phase 4: Template Generation (if needed)
1. **Gather PR Metadata**: Title, author, files changed
2. **Infer Change Type**: Based on files changed
3. **Generate Template**: Pre-fill artifact template
4. **Post Template**: Add as PR comment with instructions

### Change Detection Logic

```python
def requires_artifact(changed_files: List[str]) -> bool:
    """Determine if changes require artifact."""
    
    in_scope_patterns = [
        'src/**/*.py',
        'lib/charms/**/*.py',
        'config.yaml',
        'actions.yaml',
        'metadata.yaml',
        'charmcraft.yaml',
        '**/rockcraft.yaml',
        'requirements.txt',
        'pyproject.toml',
        '.github/workflows/*.yaml',
        'tox.ini',
        'Makefile'
    ]
    
    exempt_patterns = [
        'docs/**/*',
        'tests/**/*',
        '**/*.md',
        '.gitignore',
        '.editorconfig',
        'renovate.json'
    ]
    
    # Check exemption first
    for file in changed_files:
        if matches_any_pattern(file, exempt_patterns):
            continue
        if matches_any_pattern(file, in_scope_patterns):
            return True
    
    return False
```

### Output Format

#### Success Status
```markdown
✅ **Change Artifact Check: PASSED**

Found valid change artifact at: `docs/release-notes/artifacts/pr1234.yaml`

**Detected Changes**:
- Title: "Updated database observer for PostgreSQL 15"
- Type: minor
- Author: @contributor
- Visibility: public

All requirements met. Ready for review.
```

#### Failure Status - Missing Artifact
```markdown
❌ **Change Artifact Check: FAILED**

**Issue**: Missing change artifact

**Required**: This PR modifies in-scope files and requires a change artifact.

**Changed Files Requiring Artifact**:
- src/charm.py
- config.yaml

**Action Required**: Create `docs/release-notes/artifacts/pr1234.yaml`

### 📝 Template for Your Change Artifact

Use this template to create your change artifact:

\```yaml
# --- Release notes artifact ----

schema_version: 1
changes:
  - title: "Brief description of your change"
    author: your-github-username
    type: minor  # Options: minor, major, breaking, security, bugfix
    description: |
      Detailed description of what changed and why.
      Include context that will help users understand the impact.
    urls: 
      pr: https://github.com/canonical/indico-operator/pull/1234
      related_doc: ""
      related_issue: ""
    visibility: public  # Options: public, internal
    highlight: false  # Set to true for significant changes
\```

**Change Type Guide**:
- `minor`: New features, improvements, non-breaking changes
- `major`: Significant new features or substantial improvements
- `breaking`: Changes that break backward compatibility
- `security`: Security fixes or improvements
- `bugfix`: Bug fixes and corrections

**Examples**: See existing artifacts in `docs/release-notes/artifacts/`

**Documentation**: [Change Artifact Guide](../release-notes/template/_change-artifact-template.yaml)

---

Once you create the artifact, this check will automatically re-run.
You can also manually re-check by commenting: `check-artifact`
```

#### Failure Status - Invalid Schema
```markdown
❌ **Change Artifact Check: FAILED**

**Issue**: Invalid change artifact schema

**Found**: `docs/release-notes/artifacts/pr1234.yaml`

**Schema Errors**:
- Missing required field: `changes[0].type`
- Invalid value for `visibility`: "visible" (must be "public" or "internal")
- Field `changes[0].description` is too short (min 20 characters)

**Required Schema**:
\```yaml
schema_version: 1  # Must be 1
changes:           # Must be array with at least one item
  - title: ""      # Required, min 10 chars
    author: ""     # Required, GitHub username
    type: ""       # Required: minor|major|breaking|security|bugfix
    description: "" # Required, min 20 chars
    urls:
      pr: ""       # Required, PR URL
      related_doc: ""
      related_issue: ""
    visibility: "" # Required: public|internal
    highlight: false # Required: true|false
\```

**Fix**: Update your artifact file to match the required schema.

**Template**: See `docs/release-notes/template/_change-artifact-template.yaml`
```

#### Warning Status
```markdown
⚠️ **Change Artifact Check: PASSED WITH WARNINGS**

Found valid change artifact, but detected quality issues:

**Warnings**:
- Title is very short: "Updated code" (consider more descriptive)
- Description is minimal (consider adding more context)
- Type is "minor" but changes include breaking changes in API

**Suggestions**:
- Expand title to describe what was updated and why
- Add more details about impact and usage
- Consider changing type to "breaking" if backward compatibility affected

These are suggestions for improvement. The artifact is valid and the check passes.
```

## Exemption Process

### Automatic Exemptions
PRs are automatically exempt if:
- Only documentation files changed (docs/*, *.md)
- Only test files changed (tests/*)
- Only formatting/linting changes (no logic changes)
- Labeled with `no-changelog`

### Manual Exemptions
Apply label to PR:
- `no-changelog`: General exemption
- `docs-only`: Documentation changes only
- `tests-only`: Test changes only
- `maintenance`: Maintenance tasks (dependencies, tooling)

### Exemption Validation
Even exempt PRs are logged for audit purposes:
```markdown
ℹ️ **Change Artifact Check: EXEMPT**

**Reason**: Documentation-only changes

**Exempt Files**:
- docs/tutorial.md
- docs/reference/config.md

No change artifact required.
```

## Schema Definition

### Change Artifact Schema v1
```yaml
schema_version: 1

changes:
  - title: string                    # Required: 10-200 chars
    author: string                   # Required: GitHub username
    type: enum                       # Required: minor|major|breaking|security|bugfix
    description: string              # Required: 20-5000 chars
    urls:
      pr: string                     # Required: GitHub PR URL
      related_doc: string            # Optional: Related documentation URL
      related_issue: string          # Optional: Related issue URL
    visibility: enum                 # Required: public|internal
    highlight: boolean               # Required: true|false
    tags: array<string>              # Optional: Custom tags
    deprecations: array<object>      # Optional: Deprecated features
      - feature: string
        removal_version: string
        alternative: string
```

### Validation Rules Detail

```yaml
schema_version:
  type: integer
  allowed: [1]
  required: true

changes:
  type: array
  min_length: 1
  required: true
  
changes[].title:
  type: string
  min_length: 10
  max_length: 200
  required: true
  
changes[].author:
  type: string
  pattern: '^[a-zA-Z0-9-]+$'
  required: true
  
changes[].type:
  type: string
  enum: [minor, major, breaking, security, bugfix]
  required: true
  
changes[].description:
  type: string
  min_length: 20
  max_length: 5000
  required: true
  
changes[].urls.pr:
  type: string
  pattern: '^https://github\.com/[^/]+/[^/]+/pull/\d+$'
  required: true
  
changes[].visibility:
  type: string
  enum: [public, internal]
  required: true
  
changes[].highlight:
  type: boolean
  required: true
```

## Error Handling

### File Not Found
- Provide template in comment
- Set check status to failed
- Link to examples and documentation

### Parse Error
- Report YAML syntax error
- Show line number if available
- Suggest online YAML validator

### Schema Validation Error
- List all validation errors
- Provide corrected example
- Link to schema definition

### GitHub API Error
- Log error for debugging
- Retry with backoff
- Fall back to warning status if unable to validate

## Success Metrics

### Key Metrics
- **Compliance Rate**: % of PRs with valid artifacts
- **Time to Add Artifact**: Average time from PR open to artifact added
- **Validation Errors**: Number of schema validation failures
- **Exemption Rate**: % of PRs using exemptions

### Goals
- Achieve 95%+ compliance rate
- Reduce time to add artifact to < 30 minutes
- Keep validation errors below 10%
- Maintain exemption rate around 20-30%

## Testing Strategy

### Unit Tests
- Test file change detection logic
- Test schema validation
- Test template generation
- Test exemption logic

### Integration Tests
- Create test PRs with various change types
- Validate check status updates correctly
- Test comment generation
- Verify exemption handling

### Validation
- Run on historical PRs to tune detection
- Gather feedback on template quality
- Monitor false positive/negative rates

## Dependencies

### Required Tools
- Python 3.12
- PyYAML
- jsonschema (for validation)
- GitHub CLI (gh)

### Required Permissions
- Read access to PR files
- Write access for check status
- Comment on PRs

### GitHub API Usage
- Fetch PR files
- Update check runs
- Create/update comments

## Maintenance

### Regular Updates
- Review and update schema as needed
- Enhance detection logic based on feedback
- Improve template generation
- Update exemption rules

### Version History
- **1.0.0** (Initial): Basic artifact validation and enforcement

## Examples

### Example 1: New Feature PR
**Changes**: Added new action to config.yaml
**Result**: Artifact required and provided
**Type**: minor

### Example 2: Bug Fix PR
**Changes**: Fixed event handler in src/charm.py
**Result**: Artifact required and provided
**Type**: bugfix

### Example 3: Documentation PR
**Changes**: Updated tutorial.md and how-to guide
**Result**: Automatically exempt
**Type**: N/A

### Example 4: Dependency Update
**Changes**: requirements.txt updated by Renovate
**Result**: Artifact required (can be auto-generated)
**Type**: minor or security

## Integration with Release Process

### Release Notes Generation
1. Release manager creates release artifact in `docs/release-notes/releases/`
2. Release notes automation workflow triggered
3. Collects all change artifacts since last release
4. Generates release notes using template
5. Creates PR with generated release notes

### Change Artifact Lifecycle
```
PR Created
  ↓
Change Detection
  ↓
Artifact Required? ─→ No ─→ Exempt
  ↓ Yes
Artifact Present? ─→ No ─→ Fail Check + Template
  ↓ Yes
Schema Valid? ─→ No ─→ Fail Check + Errors
  ↓ Yes
Quality Check ─→ Warnings ─→ Pass with Warnings
  ↓ Pass
Check Passed
  ↓
PR Merged
  ↓
Artifact Available for Release
```

## Related Agents

- **Drift Agent**: Ensures documented changes match implementation
- **Dependency Update Agent**: Can auto-generate artifacts for dependency updates
- **Release Automation**: Consumes artifacts to generate release notes

## References

- [Release Notes Automation](https://github.com/canonical/release-notes-automation)
- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)
- [Change Artifact Template](../../docs/release-notes/template/_change-artifact-template.yaml)
