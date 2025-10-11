# Contributing to OpenFatture

Thank you for your interest in contributing to OpenFatture! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and professional. We're building this tool together for the Italian freelance community.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/gianlucamazza/openfatture/issues)
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version)

### Suggesting Features

1. Check existing feature requests
2. Create an issue with:
   - Use case description
   - Proposed solution
   - Alternative solutions considered

### Pull Requests

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR-USERNAME/openfatture.git
   cd openfatture
   ```

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

3. **Set Up Development Environment**
   ```bash
   # Install uv if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install dependencies
   uv sync --all-extras
   uv run pre-commit install
   ```

4. **Make Changes**
   - Write clean, documented code
   - Follow existing code style (Black, Ruff)
   - Add tests for new features
   - Update documentation

5. **Run Tests and Linters**
   ```bash
   # Format code
   uv run black .
   uv run ruff check .

   # Type checking
   uv run mypy openfatture/

   # Run tests
   uv run python -m pytest

   # Check coverage
   uv run python -m pytest --cov=openfatture
   ```

6. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   # or
   git commit -m "fix: resolve bug description"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation
   - `test:` Tests
   - `refactor:` Code refactoring
   - `chore:` Maintenance

7. **Push and Create PR**
   ```bash
   git push origin your-branch-name
   ```

   Create a Pull Request on GitHub with:
   - Clear description of changes
   - Reference related issues
   - Screenshots (if UI changes)

## Development Guidelines

### Code Style

- **Python**: Follow PEP 8, use type hints
- **Line length**: 100 characters max
- **Formatting**: Black (automatic)
- **Linting**: Ruff
- **Type checking**: MyPy

### Testing

- Write tests for all new features
- Aim for >80% code coverage
- Use pytest fixtures for common setups
- Test both success and error cases

### Documentation

- Add docstrings to all functions/classes
- Update README for new features
- Add examples for CLI commands
- Comment complex logic

### Project Structure

```
openfatture/
├── core/          # Business logic
├── sdi/           # SDI integration
├── ai/            # AI features
├── cli/           # Command-line interface
├── storage/       # Database and files
└── utils/         # Shared utilities
```

## Versioning Policy

OpenFatture follows **[Semantic Versioning 2.0.0](https://semver.org/)**.

### Version Format

Given a version number `MAJOR.MINOR.PATCH` (e.g., `1.2.3`):

- **MAJOR** version increments indicate incompatible API changes
- **MINOR** version increments add functionality in a backward-compatible manner
- **PATCH** version increments are for backward-compatible bug fixes

### When to Bump Versions

#### MAJOR (X.0.0)

Bump the major version when you make **incompatible API changes**:
- Removing or renaming public APIs
- Changing function signatures
- Breaking changes to configuration format
- Changes to database schema that require migration

**Example**: `0.9.0` → `1.0.0`

#### MINOR (0.X.0)

Bump the minor version when you add functionality in a **backward-compatible manner**:
- Adding new features
- Adding new CLI commands
- Deprecating features (but not removing them)
- Adding new database models (with migrations)

**Example**: `0.5.2` → `0.6.0`

#### PATCH (0.0.X)

Bump the patch version for **backward-compatible bug fixes**:
- Fixing bugs
- Performance improvements
- Documentation fixes

**Example**: `0.5.1` → `0.5.2`

### Version Bumping Tool

OpenFatture uses **[bump-my-version](https://github.com/callowayproject/bump-my-version)** for automated version management.

```bash
# Bump patch version (e.g., 0.1.0 → 0.1.1)
uv run bump-my-version bump patch

# Bump minor version (e.g., 0.1.0 → 0.2.0)
uv run bump-my-version bump minor

# Bump major version (e.g., 0.1.0 → 1.0.0)
uv run bump-my-version bump major

# Dry-run to see what would change
uv run bump-my-version bump patch --dry-run --verbose
```

When you bump a version, the tool automatically:
1. ✅ Updates `__version__` in `openfatture/__init__.py`
2. ✅ Updates `CHANGELOG.md` with new version header
3. ✅ Creates a git commit: `Bump version: X.Y.Z → X.Y.Z+1`
4. ✅ Creates a git tag: `vX.Y.Z+1`

After bumping, push with: `git push --follow-tags`

### Updating CHANGELOG

Before bumping a version, update `CHANGELOG.md`:
- Move items from `[Unreleased]` to new version section
- Add date: `## [0.2.0] - 2025-01-15`
- Categorize changes: Added, Changed, Fixed, Security

## Priority Areas for Contribution

We especially welcome contributions in:

### High Priority
- 🧪 **Test Coverage**: Expand test suite
- 📖 **Documentation**: User guides, examples
- 🌍 **Localization**: Support other languages
- 🔐 **Digital Signature**: Integrate signing libraries

### Medium Priority
- 🎨 **Web UI**: Optional web interface
- 📊 **Advanced Reports**: More analytics
- 🔌 **Integrations**: Banking, accounting software
- 🤖 **AI Enhancements**: Better models

### Always Welcome
- 🐛 Bug fixes
- 📝 Documentation improvements
- ✅ Test additions
- ♿ Accessibility improvements

## Questions?

- 💬 [GitHub Discussions](https://github.com/gianlucamazza/openfatture/discussions)
- 📧 Email: info@gianlucamazza.it

Thank you for contributing! 🙏
