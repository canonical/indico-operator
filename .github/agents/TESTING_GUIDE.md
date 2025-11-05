# Agent Testing and Trial Guide

This guide provides instructions for testing and validating AI automation agents before full deployment.

## Overview

Testing agents ensures they work correctly, produce accurate results, and integrate properly with existing workflows. This guide covers unit testing, integration testing, and trial procedures.

## Testing Phases

### Phase 1: Syntax and Configuration Validation
Validate that workflow files and agent definitions are correct.

### Phase 2: Unit Testing
Test individual agent components with mock data.

### Phase 3: Integration Testing
Test agents with real repository data in a controlled manner.

### Phase 4: Trial Deployment
Run agents in production with monitoring and rollback capability.

### Phase 5: Full Deployment
Enable agents for normal operation.

## Phase 1: Syntax and Configuration Validation

### Validate Workflow Syntax

```bash
# Install actionlint for workflow validation
brew install actionlint  # macOS
# or
sudo snap install actionlint  # Linux

# Validate all workflow files
actionlint .github/workflows/change_artifact_check.yaml
actionlint .github/workflows/drift_detection.yaml
actionlint .github/workflows/dependency_update_validation.yaml
```

### Validate YAML Files

```bash
# Install yamllint
pip install yamllint

# Validate workflow YAML
yamllint .github/workflows/*.yaml

# Validate agent definition syntax (Markdown with YAML examples)
# Manual review of agent definition files
```

### Check Required Files

```bash
# Verify all agent files exist
test -f .github/agents/README.md && echo "✓ README.md exists"
test -f .github/agents/AI_PLAYBOOK.md && echo "✓ AI_PLAYBOOK.md exists"
test -f .github/agents/drift-agent.md && echo "✓ drift-agent.md exists"
test -f .github/agents/dependency-update-agent.md && echo "✓ dependency-update-agent.md exists"
test -f .github/agents/change-artifact-agent.md && echo "✓ change-artifact-agent.md exists"
test -f .github/agents/LABELS_AND_CONFIG.md && echo "✓ LABELS_AND_CONFIG.md exists"
```

## Phase 2: Unit Testing

### Test Change Artifact Detection Logic

Create a test script to validate the detection logic:

```bash
# test_change_artifact_detection.sh
#!/bin/bash

# Create test changed files
echo "src/charm.py
docs/tutorial.md
requirements.txt
tests/unit/test_charm.py" > test_files.txt

# Run detection logic (extract from workflow)
python3 << 'EOF'
import re

IN_SCOPE_PATTERNS = [
    r'^src/.*\.py$',
    r'^lib/charms/.*\.py$',
    r'^config\.yaml$',
    r'^requirements\.txt$',
]

EXEMPT_PATTERNS = [
    r'^docs/.*',
    r'^tests/.*',
    r'.*\.md$',
]

def matches_pattern(file_path, patterns):
    return any(re.match(pattern, file_path) for pattern in patterns)

with open('test_files.txt', 'r') as f:
    changed_files = [line.strip() for line in f if line.strip()]

requires_artifact = False
for file_path in changed_files:
    if matches_pattern(file_path, EXEMPT_PATTERNS):
        continue
    if matches_pattern(file_path, IN_SCOPE_PATTERNS):
        requires_artifact = True
        print(f"In-scope file: {file_path}")

print(f"Requires artifact: {requires_artifact}")
assert requires_artifact == True, "Should require artifact"
print("✓ Test passed")
EOF
```

### Test Version Bump Classification

```python
# test_version_classification.py
import re

def classify_version_bump(title):
    version_pattern = r'(\d+)\.(\d+)\.(\d+).*?(?:to|→).*?(\d+)\.(\d+)\.(\d+)'
    match = re.search(version_pattern, title)
    
    if match:
        old_major, old_minor, old_patch = int(match.group(1)), int(match.group(2)), int(match.group(3))
        new_major, new_minor, new_patch = int(match.group(4)), int(match.group(5)), int(match.group(6))
        
        if new_major > old_major:
            return "major"
        elif new_minor > old_minor:
            return "minor"
        elif new_patch > old_patch:
            return "patch"
    
    return "unknown"

# Test cases
test_cases = [
    ("Update pytest from 7.4.0 to 7.4.1", "patch"),
    ("Bump django from 3.2.0 to 3.3.0", "minor"),
    ("Update package from 1.0.0 to 2.0.0", "major"),
]

for title, expected in test_cases:
    result = classify_version_bump(title)
    assert result == expected, f"Failed for '{title}': expected {expected}, got {result}"
    print(f"✓ {title} -> {result}")

print("✓ All tests passed")
```

### Test Drift Detection Parsing

```python
# test_drift_detection.py
import re
from pathlib import Path

def parse_event_handlers(charm_content):
    event_pattern = r'self\.framework\.observe\(self\.on\.(\w+),\s*self\.(\w+)\)'
    events = re.findall(event_pattern, charm_content)
    return [{'event': e[0], 'handler': e[1]} for e in events]

# Test with sample charm code
sample_charm = """
class MyCharm(CharmBase):
    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.config_changed, self._on_config_changed)
        self.framework.observe(self.on.install, self._on_install)
"""

handlers = parse_event_handlers(sample_charm)
assert len(handlers) == 2, f"Expected 2 handlers, got {len(handlers)}"
assert handlers[0]['event'] == 'config_changed'
assert handlers[1]['event'] == 'install'
print("✓ Event handler parsing test passed")
```

## Phase 3: Integration Testing

### Test Change Artifact Check on Sample PR

1. **Create a test PR with code changes and no artifact**:

```bash
# Create test branch
git checkout -b test/change-artifact-agent

# Make a small code change
echo "# Test change" >> src/state.py

# Commit and push
git add src/state.py
git commit -m "test: trigger change artifact check"
git push origin test/change-artifact-agent

# Create PR
gh pr create --title "Test: Change Artifact Agent" --body "Testing change artifact enforcement"
```

2. **Verify the workflow runs** and posts a comment with template
3. **Create the artifact** as instructed
4. **Verify the workflow passes**

### Test Drift Detection on Main Branch

1. **Trigger drift detection manually**:

```bash
# Create an issue to trigger drift detection
gh issue create \
  --title "Test: Drift Detection Scan" \
  --body "Testing drift detection agent" \
  --label "agent:drift"
```

2. **Verify the workflow runs** and posts a report
3. **Review the report** for accuracy
4. **Check for false positives**

### Test Dependency Update on Renovate PR

1. **Wait for or create a Renovate PR**
2. **Verify the agent automatically assesses** the update
3. **Check the risk assessment comment** for accuracy
4. **Verify CI wait logic** works correctly

## Phase 4: Trial Deployment

### Trial Period Setup

1. **Enable workflows** but monitor closely
2. **Set up notifications** for workflow failures
3. **Designate trial period**: 2 weeks recommended
4. **Define success criteria**:
   - Zero workflow failures
   - < 10% false positive rate
   - Positive team feedback

### Monitoring During Trial

```bash
# Monitor workflow runs
watch -n 60 'gh run list --limit 10'

# Check for failures
gh run list --status failure --limit 20

# Monitor agent comments
gh pr list --label "agent:drift,agent:dependency-updater,agent:change-artifact"
```

### Collect Feedback

Create a feedback issue:

```bash
gh issue create \
  --title "Feedback: AI Agents Trial Period" \
  --body "Please provide feedback on the AI agents:

- Change Artifact Enforcement
- Drift Detection
- Dependency Update Validation

**What's working well?**

**What needs improvement?**

**Any false positives or negatives?**

**Overall experience:**

@team" \
  --label "automation,feedback"
```

### Success Metrics

Track these metrics during the trial:

1. **Change Artifact Agent**:
   - Compliance rate (target: > 90%)
   - False positive rate (target: < 10%)
   - Time to add artifact (target: < 30 min)

2. **Drift Detection Agent**:
   - Drift items found (baseline)
   - False positive rate (target: < 15%)
   - Resolution time (target: < 1 week)

3. **Dependency Update Agent**:
   - Auto-approval rate (target: > 60%)
   - False positive rate (target: < 5%)
   - Time to assess (target: < 1 hour)

## Phase 5: Full Deployment

### Pre-deployment Checklist

- [ ] All unit tests passing
- [ ] Integration tests successful
- [ ] Trial period completed (2 weeks)
- [ ] Success metrics met
- [ ] Team feedback incorporated
- [ ] Documentation reviewed and updated
- [ ] Labels created in repository
- [ ] Branch protection configured
- [ ] Workflows enabled

### Deployment Steps

1. **Announce deployment**:

```bash
gh issue create \
  --title "Announcement: AI Agents Now Active" \
  --body "The following AI agents are now active:

- ✅ Change Artifact Enforcement
- ✅ Drift Detection  
- ✅ Dependency Update Validation

See .github/agents/README.md for usage.

Questions? Comment below." \
  --label "automation,announcement"
```

2. **Enable required checks** in branch protection
3. **Monitor for first week** closely
4. **Address issues** quickly if they arise

### Post-deployment Monitoring

```bash
# Weekly metrics collection
gh run list --workflow=change_artifact_check.yaml --created=">=2025-01-01" --json conclusion | jq '[group_by(.conclusion)[] | {conclusion: .[0].conclusion, count: length}]'

# Monthly review
# Create report of agent activity and effectiveness
```

## Rollback Procedures

### If Agent Causes Issues

1. **Immediate**: Disable workflow in repository settings
2. **Quick fix**: Update workflow to skip problematic logic
3. **Investigate**: Review logs and identify root cause
4. **Fix**: Update workflow with corrections
5. **Re-test**: Run through integration testing again
6. **Re-enable**: Only after confirming fix

### Disabling an Agent

```bash
# Disable via GitHub CLI (requires admin)
# This is done through the web UI:
# Settings -> Actions -> Disable specific workflow

# Or temporarily by removing trigger
# Edit workflow file to comment out 'on:' section
```

## Test Data and Fixtures

### Sample Change Artifacts

Create valid and invalid samples for testing:

```yaml
# Valid sample
schema_version: 1
changes:
  - title: "Test change artifact"
    author: test-user
    type: minor
    description: "This is a test change artifact for validation"
    urls:
      pr: https://github.com/canonical/indico-operator/pull/9999
      related_doc: ""
      related_issue: ""
    visibility: public
    highlight: false
```

### Sample Drift Scenarios

1. **Event handler without test**:
   - Add handler in charm.py
   - Do not add corresponding test
   - Run drift detection
   - Should report missing test

2. **Config option without docs**:
   - Add option to config.yaml
   - Do not update documentation
   - Run drift detection
   - Should report missing documentation

## Automated Testing

### GitHub Actions Test Workflow

Create a test workflow for agents:

```yaml
# .github/workflows/test_agents.yaml
name: Test Agents

on:
  pull_request:
    paths:
      - '.github/workflows/change_artifact_check.yaml'
      - '.github/workflows/drift_detection.yaml'
      - '.github/workflows/dependency_update_validation.yaml'

jobs:
  test-agents:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run agent unit tests
        run: |
          python3 test_change_artifact_detection.py
          python3 test_version_classification.py
          python3 test_drift_detection.py
```

## Continuous Improvement

### Regular Reviews

- **Monthly**: Review agent metrics and effectiveness
- **Quarterly**: Update detection rules and thresholds
- **Annually**: Comprehensive review and enhancement planning

### Enhancement Process

1. Identify improvement opportunity
2. Document proposal
3. Test in isolated environment
4. Deploy with monitoring
5. Measure impact
6. Iterate

## Support and Troubleshooting

### Common Issues

**Issue**: Workflow not triggered
- **Check**: Label spelling, workflow enabled, trigger conditions

**Issue**: False positive detections
- **Check**: Detection rules, exemption patterns, test data

**Issue**: Workflow timeout
- **Check**: CI wait time, GitHub API rate limits, dependencies

### Getting Help

1. Check workflow logs in Actions tab
2. Review agent documentation
3. Create issue with `automation` label
4. Tag `@copilot` for agent-specific issues

## Conclusion

Following this testing guide ensures agents are reliable, accurate, and beneficial to the development workflow. Regular testing and monitoring maintain agent quality over time.
