# Drift Agent Definition

## Agent Identity

- **Name**: Drift Detection and Resolution Agent
- **Label**: `agent:drift`
- **Version**: 1.0.0
- **Owner**: Platform Engineering Team

## Purpose

Detect and resolve drift between code implementations, tests, documentation, and configuration in the Indico Operator charm. Ensures that all components of the charm remain synchronized and properly documented.

## Scope

### In Scope
1. **Code vs Tests Drift**
   - Charm event handlers (on.* events) vs test coverage
   - Relation observers (database, redis, s3, saml, smtp) vs test coverage
   - Action handlers vs integration tests
   - Pebble service definitions vs tests

2. **Configuration vs Documentation Drift**
   - config.yaml options vs reference documentation
   - actions.yaml definitions vs how-to guides
   - metadata.yaml relations vs explanation docs
   - Charm parameters vs tutorial examples

3. **Implementation vs Runbooks Drift**
   - Operational procedures vs documented runbooks
   - Error handling vs troubleshooting guides
   - Configuration changes vs migration guides

### Out of Scope
- External dependency documentation
- Charmhub published documentation (read-only source)
- Upstream Indico application documentation
- Infrastructure-as-code outside this repository

## Detection Rules

### Rule 1: Event Handler Coverage
**Condition**: For each event handler in src/charm.py
**Expected**: Corresponding test in tests/integration/ or tests/unit/
**Action**: Report missing test coverage and suggest test scaffold

**Example**:
```python
# In src/charm.py
self.framework.observe(self.on.config_changed, self._on_config_changed)

# Expected in tests/
def test_config_changed(...):
    # Test implementation
```

### Rule 2: Configuration Documentation
**Condition**: For each option in config.yaml
**Expected**: Documentation in docs/reference/ or docs/explanation/
**Action**: Report missing documentation and suggest content

**Example**:
```yaml
# In config.yaml
options:
  site_url:
    type: string
    description: URL through which Indico is accessed by users.

# Expected in docs/reference/config.md or similar
## Configuration Options
### site_url
Detailed explanation of site_url configuration...
```

### Rule 3: Action Documentation
**Condition**: For each action in actions.yaml
**Expected**: Documentation in docs/how-to/ or docs/tutorial.md
**Action**: Report missing how-to guide and suggest template

**Example**:
```yaml
# In actions.yaml
add-admin:
  description: Add an admin to Indico

# Expected in docs/how-to/manage-admins.md or similar
## How to Add an Admin
Use the `add-admin` action...
```

### Rule 4: Relation Coverage
**Condition**: For each relation in metadata.yaml
**Expected**: 
- Integration test in tests/integration/
- Documentation in docs/explanation/ or docs/tutorial.md
**Action**: Report missing tests and/or documentation

### Rule 5: Observer Pattern Tests
**Condition**: For each Observer class (DatabaseObserver, S3Observer, etc.)
**Expected**: Unit tests in tests/unit/
**Action**: Report missing observer tests

## Operation Modes

### 1. Dry-Run Mode (Default)
- **Trigger**: Label `agent:drift` with comment "dry-run"
- **Behavior**: 
  - Scans for drift
  - Posts report as PR/issue comment
  - No code changes made
  - Lists all detected drift with severity

### 2. Report Mode
- **Trigger**: Label `agent:drift`
- **Behavior**:
  - Scans for drift
  - Creates detailed GitHub issue with findings
  - Categorizes drift by type and severity
  - Provides recommendations for resolution

### 3. Auto-Fix Mode
- **Trigger**: Label `agent:drift` with comment "auto-fix"
- **Behavior**:
  - Scans for drift
  - Creates PR with automatic fixes where possible:
    - Test scaffolds for missing tests
    - Documentation templates for missing docs
    - Stubs for missing implementations
  - Manual review required before merge

## Workflow

### Trigger Conditions
1. **Manual**: Apply label `agent:drift` to issue or PR
2. **Scheduled**: Weekly on Sunday at 00:00 UTC (main branch)
3. **Post-merge**: After significant code changes (optional)

### Execution Steps
1. **Checkout Repository**: Get latest code from target branch
2. **Parse Charm Code**: Extract event handlers, observers, actions
3. **Parse Configuration**: Extract config.yaml, actions.yaml, metadata.yaml
4. **Parse Tests**: Scan test files for coverage
5. **Parse Documentation**: Scan docs/ directory for references
6. **Compare and Detect**: Identify drift using detection rules
7. **Generate Report**: Create structured report of findings
8. **Take Action**: Based on operation mode (report/fix)
9. **Notify**: Comment on issue/PR or create new issue

### Output Format

#### Drift Report Structure
```markdown
# Drift Detection Report

**Date**: YYYY-MM-DD HH:MM:SS UTC
**Branch**: main
**Mode**: dry-run | report | auto-fix

## Summary
- Total drift items: X
- Critical: X
- High: X
- Medium: X
- Low: X

## Findings

### 1. Missing Test Coverage
**Severity**: High
**Category**: Code vs Tests

#### Event Handler: `_on_config_changed`
- **Location**: src/charm.py:123
- **Issue**: No corresponding test found
- **Recommendation**: Add test in tests/integration/test_charm.py
- **Suggested Test**:
  \```python
  def test_config_changed(ops_test):
      # Test implementation
  \```

### 2. Undocumented Configuration
**Severity**: Medium
**Category**: Configuration vs Documentation

#### Config Option: `external_plugins`
- **Location**: config.yaml:15
- **Issue**: Not documented in reference docs
- **Recommendation**: Add to docs/reference/configuration.md
- **Template**: See docs/reference/config-template.md

## Actions Taken
- [ ] Created PR #XXX with test scaffolds
- [ ] Created issue #YYY for documentation
- [ ] No action (dry-run mode)

## Next Steps
1. Review findings and prioritize
2. Address critical and high severity items
3. Re-run drift detection after fixes
```

## Severity Classification

### Critical
- Public actions without integration tests
- Relations without any test coverage
- Security-related code without tests

### High
- Event handlers without tests
- Configuration options without documentation
- Observers without unit tests

### Medium
- Actions without how-to guides
- Relations without explanation docs
- Complex logic without inline documentation

### Low
- Optional features without extensive docs
- Internal helpers without tests (if covered by integration tests)
- Deprecated functionality (marked for removal)

## Dependencies

### Required Tools
- Python 3.12
- Git
- GitHub CLI (gh)
- yq (YAML parser)
- PyYAML (Python library)

### Required Permissions
- Read access to repository
- Write access for PRs and issues
- Comment on PRs and issues

## Error Handling

### Parse Errors
- Log error details
- Continue with partial analysis
- Report parsing issues in output

### GitHub API Errors
- Retry with exponential backoff
- Fall back to local-only analysis
- Report API issues in workflow logs

### Analysis Failures
- Report what was successfully analyzed
- Skip failed analysis sections
- Provide diagnostic information for debugging

## Success Metrics

### Key Metrics
- **Drift Detection Rate**: Number of drift items found per scan
- **False Positive Rate**: Incorrectly identified drift items
- **Resolution Time**: Time from detection to fix
- **Coverage Improvement**: Increase in test/doc coverage over time

### Goals
- Reduce critical drift to zero within 1 sprint
- Maintain high severity drift below 5 items
- Keep false positive rate below 10%
- Improve overall coverage by 5% per quarter

## Testing Strategy

### Unit Tests
- Test drift detection logic with mock data
- Test parsing functions for each file type
- Test severity classification

### Integration Tests
- Run on sample charm repositories
- Validate report generation
- Test auto-fix mode with known drift cases

### Validation
- Manual review of drift reports on actual codebase
- Comparison with manual drift analysis
- Feedback from development team

## Maintenance

### Regular Updates
- Review and update detection rules quarterly
- Adjust severity classifications based on feedback
- Update parsing logic for new charm patterns
- Enhance auto-fix capabilities incrementally

### Version History
- **1.0.0** (Initial): Basic drift detection for events, config, and docs

## Examples

### Example 1: Missing Event Test
**Before Drift Detection:**
- `src/charm.py` has `self.framework.observe(self.on.leader_elected, self._on_leader_elected)`
- No test in `tests/` for leader_elected event

**After Drift Detection:**
- Agent creates issue reporting missing test
- Provides test scaffold in auto-fix mode

### Example 2: Undocumented Config Option
**Before Drift Detection:**
- `config.yaml` has `enable_roombooking` option
- No mention in `docs/reference/`

**After Drift Detection:**
- Agent identifies missing documentation
- Suggests documentation structure and content

### Example 3: Missing Relation Test
**Before Drift Detection:**
- `metadata.yaml` defines `s3` relation
- Only basic test exists, not comprehensive

**After Drift Detection:**
- Agent flags insufficient coverage
- Recommends additional test scenarios

## Related Agents

- **Change Artifact Enforcement Agent**: Ensures changes have release notes
- **Dependency Update Agent**: Validates dependency changes have tests
- **Test Coverage Agent** (future): Maintains coverage thresholds

## References

- [Charm Testing Guide](https://juju.is/docs/sdk/testing)
- [Documentation Standards](https://discourse.charmhub.io/t/documentation-standards/5584)
- [Operator Best Practices](https://juju.is/docs/sdk/styleguide)
