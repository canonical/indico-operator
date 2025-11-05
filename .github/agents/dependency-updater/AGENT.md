# Agent: Dependency Updater

## Purpose
Open safe dependency bump PRs (minor/patch) for Python packages, Helm charts, and charm bases with clear changelogs and a passing CI signal.

## Triggers
- Label `agent:dependency-updater` on an issue or PR, or comment: `/agent dependency-updater`
- Optional: scheduled runs (off by default).

## Scope
- Allowed:
  - `pyproject.toml`, `poetry.lock`, `requirements*.txt`
  - `helm/**/Chart.yaml`
  - `charmcraft.yaml`, `snap/snapcraft.yaml`
- Disallowed:
  - Secrets, CI credentials, infra state, workflow files.

## Inputs
- Optional allowlist at `/.config/deps-allowlist.yaml` (max version bumps, excludes).
- Optional labels to limit ecosystems: `deps:python`, `deps:helm`.

## Behavior
1. Detect outdated dependencies under constraints (prefer minor/patch).
2. Update manifests and lockfiles deterministically.
3. Open a PR including:
   - Summary and upstream release notes links.
   - Risk assessment (API changes, deprecations).
   - Test plan and local commands.
   - Rollback instructions.
4. Apply labels: `agent:dependency-updater`, `type:chore`.
5. Request review from CODEOWNERS.

## Guardrails
- PRs only; never push to protected branches.
- Require green checks `gate`, `lint`, `unit`, `package`.
- If tests fail, revert changes and summarize findings in the PR.

## Example PR title
chore(deps): bump Python/Helm dependencies (minor/patch)