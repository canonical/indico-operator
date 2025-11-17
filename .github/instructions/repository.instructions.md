# GitHub Copilot Custom Instructions for Indico Operator

## Repository Overview

This is the **Indico Operator** charm repository, a Juju operator for deploying and managing Indico (an event management system) on Kubernetes. The project follows Canonical's charm development best practices and uses Python 3.12.

## Code Standards

### Python Style
- Follow PEP 8 and use type hints
- Use descriptive variable and function names
- Prefer composition over inheritance
- Write docstrings for all public methods and classes
- Use Python 3.12 features where appropriate

### Charm Development
- Follow the [Juju Charm SDK style guide](https://juju.is/docs/sdk/styleguide)
- Follow [ISD054 - Managing Charm Complexity](https://discourse.charmhub.io/t/specification-isd014-managing-charm-complexity/11619)
- Event handlers should be clearly named (e.g., `_on_config_changed`)
- Relations should be well-documented
- Configuration options must be validated

### Testing
- Write unit tests for all charm logic
- Use pytest for testing framework
- Mock external dependencies appropriately
- Ensure integration tests cover critical workflows
- Test coverage should be comprehensive for event handlers

### Documentation
- Keep README.md up to date
- Document all configuration options in `config.yaml`
- Document all actions in `actions.yaml`
- Ensure documentation reflects actual implementation
- Update charm documentation when adding features

## Release Workflow

### Change Artifacts
All PRs that modify code or configuration **must** include a change artifact:
- Location: `docs/release-notes/artifacts/pr<PR_NUMBER>.yaml`
- Template available at: `docs/release-notes/template/_change-artifact-template.yaml`
- Required fields: `title`, `author`, `type`, `description`, `visibility`
- Types: `minor`, `major`, `breaking`, `security`, `bugfix`

**When suggesting code changes, always remind the user to create a change artifact if modifying:**
- Source code in `src/`
- Configuration in `config.yaml` or `charmcraft.yaml`
- Actions in `actions.yaml`
- Libraries in `lib/`
- Dependencies in `requirements.txt` or `pyproject.toml`

### Dependency Updates
When reviewing or suggesting dependency updates:
- Check for breaking changes in upstream release notes
- Flag any database schema changes
- Consider compatibility with current Python version (3.12)
- Note security vulnerabilities if present
- Suggest appropriate version pins

## Common Tasks

### Adding a New Event Handler
1. Define handler method in charm class
2. Register handler in `__init__` using `framework.observe()`
3. Add unit tests covering the handler
4. Document the handler's purpose and behavior
5. Update integration tests if needed

### Adding Configuration Options
1. Add option to `config.yaml` with type, default, and description
2. Implement validation in charm code
3. Handle config-changed event appropriately
4. Add tests for the new configuration
5. Document the option in README or dedicated docs

### Adding an Action
1. Define action in `actions.yaml` with parameters and description
2. Implement action handler in charm code
3. Add unit tests for the action logic
4. Provide clear error messages for failures
5. Document usage examples

## Security Considerations
- Never commit secrets or credentials
- Validate all user inputs
- Use secure defaults
- Follow principle of least privilege
- Review dependencies for known vulnerabilities

## Code Review Checklist
When reviewing code changes, consider:
- [ ] Does it follow the charm style guide?
- [ ] Are there sufficient tests?
- [ ] Is documentation updated?
- [ ] Are breaking changes clearly marked?
- [ ] Does it maintain backward compatibility where expected?
- [ ] Are error messages clear and actionable?
- [ ] Is the change artifact included (if code/config modified)?

## Getting Help
- For charm development: [Juju Discourse](https://discourse.charmhub.io/)
- For operator patterns: [Operator Framework](https://github.com/canonical/operator)
- Internal: Canonical IS Charms team

---

**Remember**: Quality over speed. Well-tested, documented code prevents future issues.
