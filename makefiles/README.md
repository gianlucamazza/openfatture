# OpenFatture Makefile System

Modular build system organised by functional area.

## 📁 Structure

```
Makefile                 # Primary orchestrator
makefiles/
├── base.mk             # Install, clean, format, lint
├── test.mk             # Testing (unit, integration, AI, payment)
├── docker.mk           # Docker & Docker Compose
├── dev.mk              # Development tools (DB, run, shell)
├── ai.mk               # AI assistant commands
├── ci.mk               # CI/CD & release management
└── media.mk            # Media automation (videos, screenshots)
```

## 🚀 Quick Start

### Core Commands

```bash
# Show categorised help
make help

# Full development setup
make dev-setup

# Install dependencies
make install

# Run full test suite
make test

# Launch OpenFatture in interactive mode
make run-interactive
```

### Categorised Help

```bash
make help-base      # Install, clean, lint, format
make help-test      # Testing commands
make help-docker    # Docker & Compose
make help-dev       # Development utilities
make help-ai        # AI tooling
make help-ci        # CI/CD
make help-media     # Media automation
make help-all       # All available commands
```

## 📚 Categories

### Base Commands (`makefiles/base.mk`)

**Installation**
```bash
make install        # Install all dependencies
make install-prod   # Production-only dependencies
make install-dev    # Dev dependencies + pre-commit hooks
make sync           # Update lockfile
```

**Cleanup**
```bash
make clean          # Clear caches and temp files
make clean-all      # Deep clean (includes build artefacts)
```

**Formatting & Linting**
```bash
make format         # Format code (black + ruff)
make lint           # Run all linters (black, ruff, mypy)
make lint-check     # Formatting check (no edits)
make type-check     # MyPy only
make pre-commit     # Run pre-commit hooks
```

### Testing Commands (`makefiles/test.mk`)

**General**
```bash
make test           # Full suite with coverage
make test-all       # Complete suite
make test-fast      # Fast subset (no coverage)
make test-watch     # Watch mode
make test-parallel  # Parallel execution
```

**Module-Specific**
```bash
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-core          # Core module tests
make test-sdi           # SDI module tests
make test-cli           # CLI tests
make test-utils         # Utility tests
```

**AI Tests**
```bash
make test-ai                # All AI tests
make test-ai-unit           # AI unit tests
make test-ai-integration    # AI integration tests
make test-ai-streaming      # Streaming tests
make test-ai-cache          # Cache tests
make test-ai-token-counter  # Token counter tests
```

**Payment Tests**
```bash
make test-payment           # Payment module (coverage ≥80%)
make test-payment-domain    # Domain tests
make test-payment-matchers  # Matcher tests
```

**Coverage**
```bash
make coverage               # Full coverage report
make coverage-report        # Open HTML report
make coverage-html          # Generate HTML only
make coverage-xml           # Generate XML (for CI)
make coverage-threshold     # Enforce threshold (80%)
```

**Shortcuts**
```bash
make t      # = test-all
make tw     # = test-watch
make tu     # = test-unit
make ti     # = test-integration
make ta     # = test-ai
make tp     # = test-payment
```

### Docker Commands (`makefiles/docker.mk`)

**Build**
```bash
make docker-build           # Build image
make docker-build-no-cache  # Build without cache
make docker-build-dev       # Build development image
```

**Run**
```bash
make docker-run         # Run container
make docker-shell       # Shell inside container
make docker-interactive # Run OpenFatture interactively
```

**Compose**
```bash
make compose-up                # Start base services
make compose-up-postgres       # Include PostgreSQL
make compose-up-ai             # Include Redis (AI cache)
make compose-up-worker         # Include payment worker
make compose-up-full           # Full stack
make compose-down              # Stop services
make compose-logs              # Tail compose logs
```

### Development Utilities (`makefiles/dev.mk`)

```bash
make dev-db-reset      # Reset local database
make dev-shell         # Drop into poetry/uv shell
make dev-run           # Run CLI entry point
make dev-lint-watch    # Watch mode linting
make dev-seed          # Seed demo data
make dev-fixtures      # Regenerate fixtures
```

### AI Commands (`makefiles/ai.mk`)

```bash
make ai-setup          # Configure AI provider prerequisites
make ai-test           # Run AI smoke tests
make ai-describe       # CLI: describe sample service
make ai-suggest-vat    # CLI: sample VAT suggestion
make ai-forecast       # CLI: sample forecast
make ai-rag-index      # Build knowledge base
make ai-rag-status     # RAG status report
```

### CI/CD (`makefiles/ci.mk`)

```bash
make ci-validate       # Run lint + tests + coverage
make ci-release        # Trigger release workflow
make ci-version        # Bump version + changelog
make ci-check-badges   # Refresh README badges
```

### Media Automation (`makefiles/media.mk`)

```bash
make media-install      # Install media tools (VHS, ffmpeg)
make media-check        # Verify prerequisites
make media-reset        # Reset demo environment
make media-scenarioA    # Generate Scenario A video
make media-scenarioB    # Scenario B video
make media-scenarioC    # Scenario C (AI) video
make media-scenarioD    # Scenario D video
make media-scenarioE    # Scenario E video
make media-all          # Generate all videos
make media-screenshots  # Capture screenshots
make media-clean        # Clean outputs
```

---

For additional context, see the individual `.mk` files or run `make help-<category>` to discover available targets.
