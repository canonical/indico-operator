# Copilot Permissions Check

This is a non-functional test file to verify GitHub Copilot automation permissions and CI gates.

## Purpose

This file was created as part of issue [#679](https://github.com/canonical/indico-operator/issues/679) to validate that Copilot automation can:
- Create and push branches to the canonical/indico-operator repository
- Open pull requests under current organization and repository protections
- Surface any required checks or review rules that apply to PRs

## Expected Behavior

This permissions probe should:
- ✅ Successfully push a new branch
- ✅ Successfully open a draft pull request
- ✅ Display any required checks or review rules on the PR (this is desirable and validates protections are working)

If DCO or signed-commit checks are enforced and fail, that outcome is acceptable and informative for this test.

## Cleanup

This file and the associated branch can be safely deleted after validation is complete.
