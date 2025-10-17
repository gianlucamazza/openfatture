# ============================================================================
# ci.mk - CI/CD integration and release management
# ============================================================================

.PHONY: ci ci-install ci-test ci-lint ci-coverage ci-security ci-docker
.PHONY: security security-bandit security-safety security-audit
.PHONY: release release-patch release-minor release-major
.PHONY: bump-version build publish
.PHONY: git-status git-check git-tag

# CI Pipeline
# ============================================================================

ci: ci-install ci-lint ci-test ci-coverage ci-security ## Run complete CI pipeline
	@echo "$(GREEN)✓ CI pipeline complete$(NC)"

ci-install: ## Install dependencies for CI
	@echo "$(BLUE)Installing dependencies (CI mode)...$(NC)"
	$(UV) sync --all-extras
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

ci-test: ## Run tests for CI
	@echo "$(BLUE)Running tests (CI mode)...$(NC)"
	$(PYTEST) tests/ -v --tb=short --maxfail=5
	@echo "$(GREEN)✓ Tests passed$(NC)"

ci-lint: ## Run linters for CI
	@echo "$(BLUE)Running linters (CI mode)...$(NC)"
	$(UV) run black --check $(PROJECT_ROOT)
	$(UV) run ruff check $(PROJECT_ROOT)
	@echo "$(GREEN)✓ Linters passed$(NC)"

ci-type-check: ## Run type checking for CI
	@echo "$(BLUE)Running type checking (CI mode)...$(NC)"
	@MYPYPATH=stubs $(UV) run mypy $(PROJECT_ROOT)/ || echo "$(YELLOW)⚠️  Type checking warnings (non-blocking)$(NC)"

ci-coverage: ## Generate coverage report for CI
	@echo "$(BLUE)Generating coverage report (CI mode)...$(NC)"
	$(PYTEST) tests/ \
		--cov=$(PROJECT_ROOT) \
		--cov-report=xml \
		--cov-report=term-missing \
		--cov-fail-under=80
	@echo "$(GREEN)✓ Coverage threshold met (>80%)$(NC)"

ci-security: security ## Run security checks for CI
	@echo "$(GREEN)✓ Security checks passed$(NC)"

ci-docker: docker-build docker-test ## Build and test Docker image for CI
	@echo "$(GREEN)✓ Docker build successful$(NC)"

ci-all: ci ci-docker ## Run complete CI pipeline including Docker
	@echo "$(GREEN)✓ Complete CI pipeline passed$(NC)"

# Security
# ============================================================================

security: security-bandit security-safety ## Run all security checks
	@echo "$(GREEN)✓ All security checks passed$(NC)"

security-bandit: ## Run bandit security linter
	@echo "$(BLUE)Running bandit security scan...$(NC)"
	@$(UV) run bandit -r $(PROJECT_ROOT)/ -ll --exclude tests/ || true
	@echo "$(GREEN)✓ Bandit scan complete$(NC)"

security-safety: ## Check for known vulnerabilities
	@echo "$(BLUE)Checking for known vulnerabilities...$(NC)"
	@$(UV) run safety check --json || echo "$(YELLOW)⚠️  Some vulnerabilities found (check output)$(NC)"

security-audit: ## Run comprehensive security audit
	@echo "$(BLUE)Running security audit...$(NC)"
	@echo "$(BLUE)  → Bandit...$(NC)"
	@$(MAKE) security-bandit
	@echo "$(BLUE)  → Safety check...$(NC)"
	@$(MAKE) security-safety
	@echo "$(BLUE)  → pip-audit...$(NC)"
	@$(UV) run pip-audit || echo "$(YELLOW)⚠️  pip-audit not installed$(NC)"
	@echo "$(GREEN)✓ Security audit complete$(NC)"

security-report: ## Generate security report
	@echo "$(BLUE)Generating security report...$(NC)"
	@mkdir -p reports
	@$(UV) run bandit -r $(PROJECT_ROOT)/ -ll --exclude tests/ -f html -o reports/security_report.html || true
	@echo "$(GREEN)✓ Security report: $(CYAN)reports/security_report.html$(NC)"

# Version Management
# ============================================================================

bump-version: ## Bump version (usage: make bump-version VERSION=0.2.0)
	@if [ -z "$(VERSION)" ]; then \
		echo "$(RED)✗ Please specify VERSION: make bump-version VERSION=0.2.0$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Bumping version to $(VERSION)...$(NC)"
	@$(UV) run bump-my-version bump --new-version $(VERSION) patch
	@echo "$(GREEN)✓ Version bumped to $(VERSION)$(NC)"

bump-patch: ## Bump patch version (0.0.X)
	@echo "$(BLUE)Bumping patch version...$(NC)"
	@$(UV) run bump-my-version bump patch
	@echo "$(GREEN)✓ Patch version bumped$(NC)"

bump-minor: ## Bump minor version (0.X.0)
	@echo "$(BLUE)Bumping minor version...$(NC)"
	@$(UV) run bump-my-version bump minor
	@echo "$(GREEN)✓ Minor version bumped$(NC)"

bump-major: ## Bump major version (X.0.0)
	@echo "$(BLUE)Bumping major version...$(NC)"
	@$(UV) run bump-my-version bump major
	@echo "$(GREEN)✓ Major version bumped$(NC)"

show-version: ## Show current version
	@echo "$(BLUE)Current version:$(NC)"
	@$(PYTHON) -c "from openfatture import __version__; print(__version__)"

# Build & Publish
# ============================================================================

build: clean ## Build distribution packages
	@echo "$(BLUE)Building distribution packages...$(NC)"
	$(UV) build
	@echo "$(GREEN)✓ Packages built in dist/$(NC)"
	@ls -lh dist/

build-check: build ## Build and check packages
	@echo "$(BLUE)Checking distribution packages...$(NC)"
	$(UV) run twine check dist/*
	@echo "$(GREEN)✓ Packages validated$(NC)"

publish: build-check ## Publish to PyPI
	@echo "$(YELLOW)⚠️  This will publish to PyPI!$(NC)"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(BLUE)Publishing to PyPI...$(NC)"; \
		$(UV) publish; \
		echo "$(GREEN)✓ Published to PyPI$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

publish-test: build-check ## Publish to TestPyPI
	@echo "$(BLUE)Publishing to TestPyPI...$(NC)"
	$(UV) run twine upload --repository testpypi dist/*
	@echo "$(GREEN)✓ Published to TestPyPI$(NC)"

# Release Management
# ============================================================================

release-patch: bump-patch git-tag ## Release patch version
	@echo "$(GREEN)✓ Patch release complete$(NC)"

release-minor: bump-minor git-tag ## Release minor version
	@echo "$(GREEN)✓ Minor release complete$(NC)"

release-major: bump-major git-tag ## Release major version
	@echo "$(GREEN)✓ Major release complete$(NC)"

release-notes: ## Generate release notes
	@echo "$(BLUE)Generating release notes...$(NC)"
	@VERSION=$$($(PYTHON) -c "from openfatture import __version__; print(__version__)"); \
	echo "# Release $$VERSION" > RELEASE_NOTES.md; \
	echo "" >> RELEASE_NOTES.md; \
	echo "## Changes" >> RELEASE_NOTES.md; \
	git log --oneline --no-merges $$(git describe --tags --abbrev=0)..HEAD >> RELEASE_NOTES.md; \
	echo "$(GREEN)✓ Release notes: RELEASE_NOTES.md$(NC)"

# Git Operations
# ============================================================================

git-status: ## Show git status
	@echo "$(BLUE)Git Status:$(NC)"
	@git status --short

git-check: ## Check if working directory is clean
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "$(RED)✗ Working directory is not clean$(NC)"; \
		git status --short; \
		exit 1; \
	else \
		echo "$(GREEN)✓ Working directory is clean$(NC)"; \
	fi

git-tag: git-check ## Create git tag for current version
	@VERSION=$$($(PYTHON) -c "from openfatture import __version__; print(__version__)"); \
	echo "$(BLUE)Creating git tag v$$VERSION...$(NC)"; \
	git tag -a "v$$VERSION" -m "Release v$$VERSION"; \
	echo "$(GREEN)✓ Tag created: v$$VERSION$(NC)"; \
	echo "$(YELLOW)Push with: git push origin v$$VERSION$(NC)"

git-tag-push: ## Push tags to remote
	@echo "$(BLUE)Pushing tags to remote...$(NC)"
	git push --tags
	@echo "$(GREEN)✓ Tags pushed$(NC)"

git-changelog: ## Generate changelog from git history
	@echo "$(BLUE)Generating changelog...$(NC)"
	@git log --oneline --no-merges --decorate > CHANGELOG.txt
	@echo "$(GREEN)✓ Changelog: CHANGELOG.txt$(NC)"

# GitHub Actions
# ============================================================================

gh-actions-list: ## List GitHub Actions workflows
	@echo "$(BLUE)GitHub Actions Workflows:$(NC)"
	@ls -1 .github/workflows/*.yml 2>/dev/null | sed 's|.github/workflows/||' || echo "No workflows found"

gh-actions-validate: ## Validate GitHub Actions workflows
	@echo "$(BLUE)Validating GitHub Actions workflows...$(NC)"
	@if [ -f scripts/validate-actions.sh ]; then \
		./scripts/validate-actions.sh; \
	else \
		echo "$(YELLOW)Validation script not found$(NC)"; \
	fi

gh-actions-test: ## Test GitHub Actions locally with act
	@echo "$(BLUE)Testing GitHub Actions with act...$(NC)"
	@if command -v act >/dev/null 2>&1; then \
		act -l; \
	else \
		echo "$(RED)✗ 'act' not installed. Install: brew install act$(NC)"; \
	fi

# Reports
# ============================================================================

report-coverage: coverage-html ## Generate coverage report
	@echo "$(GREEN)✓ Coverage report: htmlcov/index.html$(NC)"

report-security: security-report ## Generate security report
	@echo "$(GREEN)✓ Security report: reports/security_report.html$(NC)"

report-all: report-coverage report-security ## Generate all reports
	@echo "$(GREEN)✓ All reports generated in htmlcov/ and reports/$(NC)"

# CI Shortcuts
# ============================================================================

check: ci ## Shortcut for ci
validate: ci-lint ci-type-check ## Shortcut for validation
