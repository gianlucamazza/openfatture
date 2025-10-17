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
uv run python -m pytest

# With coverage
uv run python -m pytest --cov=openfatture
```

### Specific Tests

```bash
# Test specific file
uv run python -m pytest tests/test_invoice.py

# Test specific function
uv run python -m pytest tests/test_invoice.py::test_create_invoice

# Test with pattern
uv run python -m pytest -k "invoice"
```

### Coverage Report

```bash
# Terminal report
uv run python -m pytest --cov=openfatture --cov-report=term-missing

# HTML report
uv run python -m pytest --cov=openfatture --cov-report=html
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

## Web UI Development

### Setup Web UI Development Environment

```bash
# Install web dependencies
uv sync --extra web

# Run in development mode
uv run streamlit run openfatture/web/app.py --server.headless false

# Or with hot reload
STREAMLIT_SERVER_HEADLESS=false uv run streamlit run openfatture/web/app.py
```

### Web UI Architecture

The Web UI follows a **service layer pattern**:

```
openfatture/web/
├── app.py                 # Main entry point
├── pages/                 # Streamlit pages (12 pages)
├── services/              # Business logic adapters
├── components/            # Reusable UI components
├── utils/                 # Utilities (cache, async, security)
└── README.md             # Module documentation
```

### Adding New Pages

1. **Create page file** in `openfatture/web/pages/`
   ```python
   # 13_New_Feature.py
   import streamlit as st
   from openfatture.web.services import get_service

   def main():
       st.title("New Feature")
       # Your page logic here
   ```

2. **Add navigation** in `openfatture/web/navigation.py`
   ```python
   pages = {
       "📊 Business": [dashboard, invoices, clients, new_feature],
       # ...
   }
   ```

3. **Add service layer** if needed
   ```python
   # openfatture/web/services/new_feature_service.py
   from openfatture.core import business_logic

   def get_new_feature_data():
       # Adapter to core business logic
       pass
   ```

### Component Development

Use the **reusable component library**:

```python
from openfatture.web.components import metric_card, data_table, success_alert

# Metric card with delta
metric_card("Revenue", "€10,000", delta="+15%", icon="💰")

# Data table with actions
data_table(data, columns=["name", "value"],
          actions=[{"icon": "✏️", "callback": edit_item}])

# Success notification
success_alert("Operation completed successfully!")
```

### Caching Strategy

```python
import streamlit as st
from openfatture.web.utils.cache import cache_with_ttl, invalidate_cache_by_category

# TTL-based caching
@cache_with_ttl(ttl_seconds=300)  # 5 minutes
def get_dashboard_data():
    return expensive_query()

# Selective invalidation
invalidate_cache_by_category("invoices")  # Only clear invoice caches
```

### Testing Web UI

```bash
# Run all web tests
uv run python -m pytest tests/web/ -v

# Run specific component tests
uv run python -m pytest tests/web/utils/test_cache.py -v

# Coverage report
uv run python -m pytest tests/web/ --cov=openfatture.web --cov-report=html
```

### Debugging Web UI

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check session state
st.write(st.session_state)

# Clear all caches
st.cache_data.clear()
st.cache_resource.clear()
```

### Performance Optimization

1. **Use appropriate cache TTLs**
   - Real-time data: 30-60 seconds
   - User data: 5-10 minutes
   - Static config: 1 hour+

2. **Lazy loading for large datasets**
   ```python
   if st.button("Load Details"):
       data = load_large_dataset()  # Only load when requested
   ```

3. **Pagination for tables**
   ```python
   page_size = 50
   page = st.number_input("Page", min_value=1, value=1)
   offset = (page - 1) * page_size
   data = get_data(limit=page_size, offset=offset)
   ```

### Security Best Practices

```python
from openfatture.web.utils.security import validate_file_upload, sanitize_html

# File upload validation
is_valid, error = validate_file_upload(
    uploaded_file,
    allowed_extensions=["pdf", "png"],
    max_size_mb=10
)
if not is_valid:
    st.error(error)

# HTML sanitization
safe_html = sanitize_html(user_input)
st.markdown(safe_html, unsafe_allow_html=True)
```

### Deployment

```bash
# Production build
uv run streamlit run openfatture/web/app.py \
  --server.address 0.0.0.0 \
  --server.port 8501 \
  --server.fileWatcherType none

# Docker deployment
docker build -t openfatture-web .
docker run -p 8501:8501 openfatture-web
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
# Bump patch version (1.0.0 → 1.0.1)
uv run bump-my-version bump patch

# Bump minor version (1.0.0 → 1.1.0)
uv run bump-my-version bump minor

# Bump major version (1.0.0 → 2.0.0)
uv run bump-my-version bump major

# Dry-run to preview changes
uv run bump-my-version bump patch --dry-run --verbose
```

This automatically:
1. ✅ Updates `__version__` in `openfatture/__init__.py`
2. ✅ Updates `CHANGELOG.md`
3. ✅ Creates git commit
4. ✅ Creates git tag `v<new-version>`

### Pre-release Checklist

Before bumping version:

- [ ] All tests pass: `uv run python -m pytest`
- [ ] Code formatted: `uv run black --check .`
- [ ] No lint errors: `uv run ruff check .`
- [ ] CHANGELOG.md updated with changes
- [ ] Documentation updated (`docs/README.md`, release notes, README badges)
- [ ] GitHub Actions validated: `./scripts/validate-actions.sh`

### Creating a Release

1. **Update CHANGELOG.md**:
   ```markdown
   ## [Unreleased]

   ## [1.1.0] - 2026-01-15
   ### Added
   - New interactive dashboard
   - Batch operations
   ### Fixed
   - Fixed validation error
   ```

2. **Aggiorna la documentazione di rilascio**:
   - Duplica `docs/releases/<versione-precedente>.md` come base per la nuova release.
   - Aggiorna `docs/README.md` e il README principale con link e badge della nuova versione.

3. **Bump version**:
   ```bash
   uv run bump-my-version bump minor
   ```

4. **Push con tag**:
   ```bash
   git push --follow-tags
   ```

5. **GitHub Actions will automatically**:
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
uv run python -m pytest tests/test_invoice.py

# 4. Format and commit
uv run black .
git commit -am "feat: my changes"
```

### Debugging Tests

```bash
# Verbose pytest output
uv run python -m pytest -v

# Show print statements
uv run python -m pytest -s

# Drop into debugger on failure
uv run python -m pytest --pdb
```

### Performance Profiling

```bash
# Profile test execution
uv run python -m pytest --durations=10
```

### AI Cash Flow Predictor (Prophet + XGBoost)

- I modelli vengono salvati in `MLConfig.model_path` (default `.models/`) con i file:
  - `cash_flow_prophet.json` / `cash_flow_xgboost.json` (ensemble)
  - `cash_flow_pipeline.pkl` (feature pipeline + scaler)
  - `cash_flow_metrics.json` (metriche MAE/RMSE, coverage, metadata dataset)
- Per rigenerare i modelli esegui:
  ```bash
  uv run openfatture ai forecast --retrain
  ```
- Assicurati che il database contenga almeno 25 fatture/pagamenti reali; in caso contrario il training viene interrotto con errore.
- Dopo modifiche al codice ML lancia i test dedicati:
  ```bash
  uv run pytest tests/ai/test_cash_flow_predictor_training.py
  ```
- Puoi ispezionare metriche e dataset utilizzati aprendo `cash_flow_metrics.json`.

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
