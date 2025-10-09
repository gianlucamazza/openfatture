# Development Guide

Complete guide for OpenFatture development environment setup, testing, and CI/CD workflows.

## Table of Contents

- [Development Environment Setup](#development-environment-setup)
- [Testing GitHub Actions Locally](#testing-github-actions-locally)
- [Running Tests](#running-tests)
- [Code Quality](#code-quality)
- [Git Workflow](#git-workflow)
- [Release Process](#release-process)

---

## Development Environment Setup

### Prerequisites

- **Python 3.12+**: [Download](https://www.python.org/downloads/)
- **uv**: Fast Python package manager
- **Git**: Version control
- **act** (optional): For testing GitHub Actions locally

### Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/gianlucamazza/openfatture.git
cd openfatture

# Install all dependencies (including dev tools)
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install

# Initialize database
uv run python -c "from openfatture.storage.database.session import init_db; init_db()"
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit with your settings
nano .env
```

See [CONFIGURATION.md](CONFIGURATION.md) for all available options.

---

## Testing GitHub Actions Locally

OpenFatture uses **[act](https://github.com/nektos/act)** to test GitHub Actions workflows locally before pushing to GitHub.

### Why act?

✅ **Fast feedback**: Test workflows before pushing
✅ **Debug locally**: No trial-and-error on GitHub
✅ **Cost savings**: Zero GitHub Actions minutes consumed
✅ **CI/CD confidence**: Validate workflows work correctly

### Installing act

```bash
# macOS (Homebrew)
brew install act

# Linux (script)
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Or download from: https://github.com/nektos/act/releases
```

Verify installation:

```bash
act --version
# Should output: act version 0.2.x
```

### Setup for Local Testing

#### Option 1: Automatic Setup with GitHub CLI (Recommended)

If you have **GitHub CLI (`gh`)** installed and authenticated, secrets are configured automatically:

```bash
# Install GitHub CLI (if not already installed)
brew install gh

# Authenticate (one-time setup)
gh auth login

# Run any act command - secrets are auto-configured!
./scripts/validate-actions.sh
./scripts/test-actions.sh lint
```

**What happens automatically:**
- ✅ GITHUB_TOKEN extracted from `gh auth token`
- ✅ `.secrets` file created/updated automatically
- ✅ Token always up-to-date (no manual management)
- ✅ Zero configuration needed

#### Option 2: Manual Setup

If you don't have GitHub CLI, you can configure secrets manually:

1. **Copy secrets template**:
   ```bash
   cp .secrets.example .secrets
   ```

2. **Edit `.secrets` with test values**:
   ```bash
   nano .secrets
   ```

   **Important considerations:**
   - The `.secrets` file is git-ignored
   - For **validation only** (syntax check, dry-run): fake tokens work fine
   - For **full workflow execution**: you need a real GitHub token

   Example for validation (fake tokens):
   ```
   GITHUB_TOKEN=ghp_FAKE_TOKEN_FOR_LOCAL_TESTING
   PYPI_TOKEN=pypi-FAKE_TOKEN_FOR_LOCAL_TESTING
   CODECOV_TOKEN=FAKE_CODECOV_TOKEN
   ```

   For full execution testing:
   ```
   # Get a personal access token at: https://github.com/settings/tokens
   # Required scope: repo (for cloning GitHub Actions)
   GITHUB_TOKEN=ghp_your_real_github_token_here
   PYPI_TOKEN=pypi-FAKE_TOKEN_FOR_LOCAL_TESTING  # Still use fake for PyPI
   CODECOV_TOKEN=FAKE_CODECOV_TOKEN
   ```

#### Configuration Files
   - `.actrc`: act configuration (already configured)
   - `.env.act`: Environment variables for simulation (already configured)
   - `test-event.json`: Mock event for release workflow testing

### Validation Commands

#### Quick Validation

```bash
# Validate all workflows (syntax check + dry-run)
./scripts/validate-actions.sh
```

This script:
1. ✅ Checks workflow syntax
2. ✅ Dry-runs test workflow
3. ✅ Dry-runs release workflow
4. ✅ Warns about missing secrets

#### List All Jobs

```bash
# See all jobs in all workflows
act -l

# Output example:
# Stage  Job         Workflow
# 0      test        Test
# 0      lint        Test
# 0      security    Test
# 1      coverage    Test
```

#### Dry-Run (No Execution)

```bash
# Dry-run test workflow
act push --dryrun -W .github/workflows/test.yml

# Dry-run release workflow
act push --dryrun -W .github/workflows/release.yml --eventpath test-event.json
```

### Running Workflows

#### Fast Tests (Lint Only)

```bash
# Run lint job (fastest way to test)
act push -j lint

# Or use the script:
./scripts/test-actions.sh lint
```

#### Run Specific Jobs

```bash
# Test job with specific Python version
act push -j test --matrix python-version:3.12 --matrix os:ubuntu-latest

# Security scan
act push -j security

# Coverage gate
act push -j coverage-gate

# Or use the script:
./scripts/test-actions.sh test
./scripts/test-actions.sh security
./scripts/test-actions.sh coverage
```

#### Run Complete Workflows

```bash
# All test jobs (takes several minutes)
act push -W .github/workflows/test.yml

# Or use the script:
./scripts/test-actions.sh all
```

#### Test Release Workflow

```bash
# Simulate a version tag push
act push -W .github/workflows/release.yml --eventpath test-event.json

# Or use the script:
./scripts/test-actions.sh release
```

### Debugging Workflows

#### Verbose Output

```bash
act push -j lint --verbose
```

#### Interactive Shell

```bash
# Drop into an interactive shell within the workflow
act push -j lint --shell
```

#### Rebuild Without Cache

```bash
act push -j lint --rebuild
```

#### View Logs

```bash
# Act creates logs in /tmp
# Check Docker containers:
docker ps -a

# View logs of a specific container:
docker logs <container-id>
```

### act Limitations

⚠️ **Important limitations to be aware of**:

1. **GitHub Actions require authentication**:
   - Remote actions (like `astral-sh/setup-uv@v1`) need a real GITHUB_TOKEN
   - Validation and dry-run work with fake tokens
   - Full execution requires a GitHub personal access token
   - Get token at: https://github.com/settings/tokens (scope: `repo`)

2. **No macOS runner**: act uses Linux containers even for `macos-latest`

3. **Docker required**: All jobs run in Docker containers

4. **Some actions unsupported**:
   - `upload-artifact`: Partial support
   - `download-artifact`: Partial support
   - Some GitHub-specific actions may not work

5. **Secrets**:
   - Use fake/test values for PyPI, Codecov, etc.
   - GITHUB_TOKEN needs to be real for full execution
   - Never commit real credentials

6. **Network**: Some services may not be accessible from containers

### Common Issues & Solutions

#### Issue: "secrets file not found"

**Solution**: Copy `.secrets.example` to `.secrets`:
```bash
cp .secrets.example .secrets
```

#### Issue: "Docker daemon not running"

**Solution**: Start Docker Desktop or Docker daemon:
```bash
# macOS
open -a Docker

# Linux
sudo systemctl start docker
```

#### Issue: "Permission denied" on scripts

**Solution**: Make scripts executable:
```bash
chmod +x scripts/*.sh
```

#### Issue: Workflow hangs or is slow

**Solution**:
1. Use specific jobs instead of complete workflows: `act push -j lint`
2. Use dry-run for validation: `act push --dryrun`
3. Increase Docker resources (CPU/Memory)

#### Issue: "Image pull failed"

**Solution**: Pull the image manually first:
```bash
docker pull catthehacker/ubuntu:act-latest
```

#### Issue: "authentication required" when cloning GitHub Actions

**Problem**: act can't clone remote GitHub Actions (like `astral-sh/setup-uv@v1`)

**Solution**: Create a GitHub personal access token:
```bash
# 1. Generate token at: https://github.com/settings/tokens
#    Required scope: repo
# 2. Update .secrets with real token:
GITHUB_TOKEN=ghp_your_real_token_here
# 3. Re-run act
```

**Alternative**: Use `--dryrun` flag for validation without execution:
```bash
act push --dryrun -W .github/workflows/test.yml
```

---

## Running Tests

### Quick Test

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=openfatture
```

### Specific Tests

```bash
# Test specific file
uv run pytest tests/test_invoice.py

# Test specific function
uv run pytest tests/test_invoice.py::test_create_invoice

# Test with pattern
uv run pytest -k "invoice"
```

### Coverage Report

```bash
# Terminal report
uv run pytest --cov=openfatture --cov-report=term-missing

# HTML report
uv run pytest --cov=openfatture --cov-report=html
open htmlcov/index.html
```

### Watch Mode

```bash
# Install pytest-watch
uv add --dev pytest-watch

# Run in watch mode
uv run ptw
```

---

## Code Quality

### Formatting

```bash
# Format all code with Black
uv run black .

# Check formatting without changes
uv run black --check .
```

### Linting

```bash
# Run Ruff linter
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .
```

### Type Checking

```bash
# Run MyPy type checker
uv run mypy openfatture/
```

### Pre-commit Hooks

All code quality checks run automatically before commit:

```bash
# Manually run all hooks
uv run pre-commit run --all-files
```

---

## Git Workflow

### Branch Strategy

- `main`: Stable production branch
- `develop`: Development branch (if used)
- `feature/*`: New features
- `fix/*`: Bug fixes
- `release/*`: Release preparation

### Creating a Feature Branch

```bash
# Create and switch to feature branch
git checkout -b feature/my-new-feature

# Make changes
# ...

# Stage and commit
git add .
git commit -m "feat: add new feature description"

# Push to remote
git push -u origin feature/my-new-feature
```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting, missing semicolons, etc
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```bash
git commit -m "feat: add interactive dashboard"
git commit -m "fix: correct VAT calculation for reverse charge"
git commit -m "docs: update quickstart guide"
```

---

## Release Process

### Version Bumping

OpenFatture uses **bump-my-version** for automated version management.

```bash
# Bump patch version (0.1.0 → 0.1.1)
uv run bump-my-version bump patch

# Bump minor version (0.1.0 → 0.2.0)
uv run bump-my-version bump minor

# Bump major version (0.1.0 → 1.0.0)
uv run bump-my-version bump major

# Dry-run to preview changes
uv run bump-my-version bump patch --dry-run --verbose
```

This automatically:
1. ✅ Updates `__version__` in `openfatture/__init__.py`
2. ✅ Updates `CHANGELOG.md`
3. ✅ Creates git commit
4. ✅ Creates git tag `v0.1.1`

### Pre-release Checklist

Before bumping version:

- [ ] All tests pass: `uv run pytest`
- [ ] Code formatted: `uv run black --check .`
- [ ] No lint errors: `uv run ruff check .`
- [ ] CHANGELOG.md updated with changes
- [ ] Documentation updated
- [ ] GitHub Actions validated: `./scripts/validate-actions.sh`

### Creating a Release

1. **Update CHANGELOG.md**:
   ```markdown
   ## [Unreleased]

   ## [0.2.0] - 2025-01-15
   ### Added
   - New interactive dashboard
   - Batch operations
   ### Fixed
   - Fixed validation error
   ```

2. **Bump version**:
   ```bash
   uv run bump-my-version bump minor
   ```

3. **Push with tags**:
   ```bash
   git push --follow-tags
   ```

4. **GitHub Actions will automatically**:
   - Run all tests
   - Build package
   - Create GitHub Release
   - Publish to PyPI (if configured)

### Manual Release (if needed)

```bash
# Build package
uv build

# Verify contents
ls -lh dist/

# Publish to PyPI (requires PYPI_TOKEN)
uvx twine upload dist/*
```

---

## Development Tips

### Fast Iteration

```bash
# 1. Make code changes
# 2. Quick validation
act push -j lint

# 3. Run specific test
uv run pytest tests/test_invoice.py

# 4. Format and commit
uv run black .
git commit -am "feat: my changes"
```

### Debugging Tests

```bash
# Verbose pytest output
uv run pytest -v

# Show print statements
uv run pytest -s

# Drop into debugger on failure
uv run pytest --pdb
```

### Performance Profiling

```bash
# Profile test execution
uv run pytest --durations=10
```

---

## Additional Resources

- [Contributing Guide](../CONTRIBUTING.md)
- [Quick Start](QUICKSTART.md)
- [Configuration Reference](CONFIGURATION.md)
- [Email Templates](EMAIL_TEMPLATES.md)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [act Documentation](https://github.com/nektos/act)

---

## Getting Help

- 💬 [GitHub Discussions](https://github.com/gianlucamazza/openfatture/discussions)
- 🐛 [GitHub Issues](https://github.com/gianlucamazza/openfatture/issues)
- 📧 Email: info@gianlucamazza.it
