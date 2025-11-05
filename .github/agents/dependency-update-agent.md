# Dependency Update Agent Definition

## Agent Identity

- **Name**: Dependency Update Validation Agent
- **Label**: `agent:dependency-updater`
- **Version**: 1.0.0
- **Owner**: Platform Engineering Team

## Purpose

Automate validation and risk assessment of dependency updates created by Renovate (or other dependency management tools). Ensures all dependency updates are safe, tested, and properly documented before merge.

## Scope

### In Scope
1. **Python Dependencies**
   - requirements.txt updates
   - pyproject.toml dependency changes
   - tox.ini test dependencies

2. **Charm Libraries**
   - lib/charms/* library updates
   - Operator framework updates

3. **Base Images**
   - rockcraft.yaml base image references
   - OCI image updates (indico-image, indico-nginx-image)

4. **Terraform Providers**
   - terraform/providers.tf updates
   - Juju provider version changes

5. **GitHub Actions**
   - .github/workflows/* action version updates

### Out of Scope
- Upstream Indico application dependencies (managed separately)
- Development tool updates (unless they affect CI/CD)
- Documentation-only updates
- Manual dependency changes not from Renovate

## Validation Rules

### Rule 1: CI Must Pass
**Condition**: All CI checks must pass
**Checks**:
- Unit tests (tox -e unit)
- Lint checks (tox -e lint)
- Plugins tests (tox -e plugins)
- Integration tests (if applicable)
- Charm packaging (charmcraft pack)

**Action**: Block merge if any check fails, add comment with failure details

### Rule 2: Security Scan Required
**Condition**: New dependencies must be scanned for vulnerabilities
**Checks**:
- GitHub Advisory Database check
- Trivy vulnerability scan
- Known CVE check

**Action**: 
- Block if critical vulnerabilities found
- Warn if high vulnerabilities found
- Report medium/low vulnerabilities
- Provide mitigation recommendations

### Rule 3: Version Bump Policy
**Condition**: Version changes must follow semantic versioning policy
**Policy**:
- **Patch versions (x.x.X)**: Auto-approve if CI passes
- **Minor versions (x.X.0)**: Review required, auto-approve if CI passes and no breaking changes
- **Major versions (X.0.0)**: Manual review required, detailed changelog needed

**Action**: Label PR with version bump type, add appropriate reviewers

### Rule 4: Upstream Changelog
**Condition**: Must include upstream changelog summary
**Required Information**:
- Link to upstream release notes
- Summary of changes (features, fixes, breaking changes)
- Migration notes if applicable
- Impact assessment

**Action**: Add changelog comment to PR, request manual review if breaking changes

### Rule 5: Rollback Plan
**Condition**: Must have rollback capability
**Requirements**:
- Previous version known and documented
- Rollback procedure documented
- Automated rollback on CI failure

**Action**: Document rollback command in PR comment

## Operation Modes

### 1. Automatic Monitoring (Default)
- **Trigger**: Automatically monitors all Renovate PRs
- **Behavior**:
  - Validates CI status
  - Runs security scans
  - Adds risk assessment comment
  - Auto-approves safe updates (patch versions)
  - Requests review for risky updates

### 2. Manual Validation
- **Trigger**: Label `agent:dependency-updater` on PR
- **Behavior**:
  - Runs full validation suite
  - Generates detailed report
  - Posts assessment as PR comment
  - No automatic actions

### 3. Rollback Mode
- **Trigger**: Comment "rollback-dependency" on failed PR
- **Behavior**:
  - Creates new PR reverting dependency change
  - Documents reason for rollback
  - Alerts maintainers

## Workflow

### Trigger Conditions
1. **Automatic**: PR created by Renovate bot
2. **Manual**: Label `agent:dependency-updater` applied
3. **Scheduled**: Daily scan for new dependency updates (optional)

### Execution Steps

#### Phase 1: Initial Assessment
1. **Identify Changes**: Parse PR diff for dependency changes
2. **Classify Update**: Determine version bump type (patch/minor/major)
3. **Check Author**: Verify PR is from Renovate or trusted source

#### Phase 2: Security Validation
1. **Vulnerability Scan**: Check new versions for known CVEs
2. **Advisory Check**: Query GitHub Advisory Database
3. **License Compliance**: Verify license compatibility
4. **Supply Chain**: Check for suspicious packages or maintainers

#### Phase 3: CI Validation
1. **Wait for CI**: Monitor workflow runs
2. **Check Results**: Validate all required checks pass
3. **Analyze Failures**: Provide detailed failure analysis if needed

#### Phase 4: Risk Assessment
1. **Gather Changelog**: Fetch upstream release notes
2. **Identify Breaking Changes**: Scan for breaking changes
3. **Assess Impact**: Evaluate impact on charm functionality
4. **Calculate Risk Score**: Generate risk rating (low/medium/high/critical)

#### Phase 5: Recommendation
1. **Generate Report**: Create comprehensive assessment
2. **Add Comment**: Post to PR with recommendation
3. **Auto-approve or Request Review**: Based on risk level
4. **Notify Team**: Alert on high-risk updates

### Risk Assessment Matrix

| Version Bump | Security Issues | CI Status | Risk Level | Action |
|--------------|----------------|-----------|------------|--------|
| Patch | None | Pass | Low | Auto-approve |
| Patch | Low | Pass | Low | Auto-approve |
| Patch | Medium+ | Pass | Medium | Manual review |
| Patch | Any | Fail | High | Block |
| Minor | None | Pass | Low | Auto-approve |
| Minor | Low | Pass | Medium | Manual review |
| Minor | Medium+ | Pass | High | Block |
| Minor | Any | Fail | High | Block |
| Major | Any | Pass | High | Manual review |
| Major | Any | Fail | Critical | Block |

### Output Format

#### Risk Assessment Comment
```markdown
## 🤖 Dependency Update Assessment

**Update Type**: Patch | Minor | Major
**Package**: package-name
**Version Change**: 1.2.3 → 1.2.4
**Risk Level**: 🟢 Low | 🟡 Medium | 🟠 High | 🔴 Critical

### Security Scan Results
✅ No known vulnerabilities
⚠️ 1 medium severity vulnerability found: CVE-XXXX-XXXXX
🚨 Critical vulnerability: CVE-YYYY-YYYYY

### CI Status
✅ All checks passed
- ✅ Unit tests
- ✅ Lint checks
- ✅ Integration tests
- ✅ Packaging

### Upstream Changelog
**Release Notes**: https://github.com/org/repo/releases/tag/v1.2.4

**Summary of Changes**:
- Fixed bug in feature X
- Performance improvement for Y
- Updated dependency Z

**Breaking Changes**: None

**Migration Notes**: None required

### Impact Assessment
- **Code Changes Required**: No
- **Configuration Changes**: No
- **Documentation Updates**: No
- **Test Updates**: No

### Risk Factors
- ✅ Patch version update (low risk)
- ✅ No breaking changes
- ✅ All tests pass
- ✅ No security issues

### Recommendation
✅ **APPROVED**: Safe to merge after review

**Rollback Plan**:
If issues occur after merge, rollback with:
\```bash
# Revert to previous version
pip install package-name==1.2.3
# Or use git revert
git revert <commit-hash>
\```

### Additional Notes
This is a routine patch update with bug fixes and improvements. No action required beyond standard review process.

---
*Generated by Dependency Update Agent v1.0.0*
*For questions or issues, consult `.github/agents/AI_PLAYBOOK.md`*
```

## Renovate Integration

### Renovate Configuration
The agent automatically monitors PRs with:
- Author: `renovate[bot]`
- Branch pattern: `renovate/*`
- Labels: `renovate`, `dependencies`

### Enhanced Renovate Settings
Add to `renovate.json`:
```json
{
  "labels": ["renovate", "dependencies"],
  "assignees": ["@team-platform"],
  "reviewers": ["@team-platform"],
  "prCreation": "not-pending",
  "minimumReleaseAge": "3 days",
  "semanticCommits": "enabled"
}
```

### Auto-merge Criteria
Auto-merge is enabled for:
- Patch updates with CI passing
- No security vulnerabilities
- No breaking changes detected
- Risk level: Low

## Security Guidelines

### Vulnerability Response

#### Critical Vulnerabilities
- **Action**: Block PR immediately
- **Notification**: Alert security team
- **Resolution**: Wait for patched version or find alternative

#### High Vulnerabilities
- **Action**: Block PR, request security review
- **Notification**: Alert maintainers
- **Resolution**: Assess risk vs. benefit, may require manual patching

#### Medium Vulnerabilities
- **Action**: Allow with manual review
- **Notification**: Comment on PR
- **Resolution**: Plan mitigation in near-term

#### Low Vulnerabilities
- **Action**: Allow with documentation
- **Notification**: Track in issue
- **Resolution**: Address in future update cycle

### Supply Chain Security
- Verify package source and maintainer reputation
- Check for recent ownership changes
- Monitor for unusual dependency additions
- Scan for typosquatting attempts

## Error Handling

### CI Timeout
- Wait up to 2 hours for CI completion
- If timeout, add comment requesting manual check
- Do not block or approve

### GitHub API Rate Limit
- Implement exponential backoff
- Queue requests for retry
- Notify if critical API calls fail

### Parse Errors
- Log error details for debugging
- Continue with partial validation
- Mark as requiring manual review

### Upstream Unavailable
- Use cached changelog if available
- Mark as requiring manual changelog addition
- Proceed with other validations

## Success Metrics

### Key Metrics
- **Auto-approval Rate**: % of updates auto-approved
- **False Positive Rate**: % of approved updates causing issues
- **Time to Merge**: Average time from PR creation to merge
- **Security Catch Rate**: % of vulnerabilities caught before merge
- **Rollback Rate**: % of updates requiring rollback

### Goals
- Auto-approve 70%+ of patch updates
- Keep false positive rate below 5%
- Reduce time to merge to < 24 hours for safe updates
- Catch 100% of critical/high vulnerabilities
- Maintain rollback rate below 2%

## Testing Strategy

### Unit Tests
- Test risk calculation logic
- Test version bump classification
- Test changelog parsing

### Integration Tests
- Create test PRs with various dependency updates
- Validate risk assessment accuracy
- Test auto-approval workflow
- Verify security scan integration

### Validation
- Run on historical dependency PRs
- Compare assessments with actual outcomes
- Gather feedback from team on accuracy

## Dependencies

### Required Tools
- Python 3.12
- GitHub CLI (gh)
- pip-audit or safety (security scanning)
- jq/yq (JSON/YAML parsing)

### Required Permissions
- Read access to repository
- Write access for PR comments
- Ability to request reviews
- Ability to approve PRs (with appropriate role)

### External Services
- GitHub Advisory Database
- Upstream package registries (PyPI, etc.)
- Trivy vulnerability database

## Maintenance

### Regular Updates
- Update vulnerability databases weekly
- Review and adjust risk matrix quarterly
- Enhance changelog parsing for new formats
- Update Renovate integration as needed

### Version History
- **1.0.0** (Initial): Basic dependency validation and risk assessment

## Examples

### Example 1: Safe Patch Update
**PR**: Update pytest from 7.4.0 to 7.4.1
**Assessment**: Low risk, auto-approved
**Result**: Merged automatically after CI passed

### Example 2: Minor Update with Changes
**PR**: Update ops from 2.9.0 to 2.10.0
**Assessment**: Medium risk, manual review requested
**Result**: Reviewed by team, merged after discussion

### Example 3: Major Update Blocked
**PR**: Update Django from 3.x to 4.x (hypothetical)
**Assessment**: Critical risk due to major version
**Result**: Blocked pending detailed migration plan

### Example 4: Security Vulnerability Found
**PR**: Update requests from 2.28.0 to 2.28.1
**Assessment**: High risk due to known CVE
**Result**: Blocked, alternative version found and proposed

## Related Agents

- **Drift Agent**: Ensures updated dependencies have corresponding tests
- **Change Artifact Enforcement Agent**: Requires release notes for dependency changes
- **Security Audit Agent** (future): Comprehensive security scanning

## References

- [Renovate Documentation](https://docs.renovatebot.com/)
- [GitHub Advisory Database](https://github.com/advisories)
- [Semantic Versioning](https://semver.org/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
