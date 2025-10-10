# ============================================================================
# base.mk - Base development tasks (install, clean, format, lint)
# ============================================================================

.PHONY: install install-prod install-dev sync clean clean-all format lint lint-check type-check pre-commit

# Installation targets
# ============================================================================

install: check-uv ## Install all dependencies (production + dev)
	@echo "$(BLUE)Installing all dependencies...$(NC)"
	$(UV) sync --all-extras
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-prod: check-uv ## Install production dependencies only
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	$(UV) sync --no-dev
	@echo "$(GREEN)✓ Production dependencies installed$(NC)"

install-dev: check-uv ## Install dev dependencies
	@echo "$(BLUE)Installing dev dependencies...$(NC)"
	$(UV) sync --all-extras
	$(UV) run pre-commit install
	@echo "$(GREEN)✓ Dev dependencies installed$(NC)"

sync: check-uv ## Sync dependencies (update lockfile)
	@echo "$(BLUE)Syncing dependencies...$(NC)"
	$(UV) sync
	@echo "$(GREEN)✓ Dependencies synced$(NC)"

# Cleanup targets
# ============================================================================

clean: ## Clean cache and temp files
	@echo "$(BLUE)Cleaning cache and temp files...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".hypothesis" -exec rm -rf {} + 2>/dev/null || true
	@rm -f .coverage 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned$(NC)"

clean-all: clean ## Clean everything including build artifacts and venv
	@echo "$(BLUE)Deep cleaning...$(NC)"
	@rm -rf dist/ build/ htmlcov/ .eggs/ 2>/dev/null || true
	@rm -rf .venv/ .tox/ 2>/dev/null || true
	@echo "$(GREEN)✓ Deep clean complete$(NC)"

# Code formatting
# ============================================================================

format: ## Format code with black and ruff
	@echo "$(BLUE)Formatting code...$(NC)"
	$(UV) run black $(PROJECT_ROOT)
	$(UV) run ruff check $(PROJECT_ROOT) --fix
	@echo "$(GREEN)✓ Code formatted$(NC)"

# Code linting
# ============================================================================

lint: lint-check type-check ## Run all linters (black, ruff, mypy)
	@echo "$(GREEN)✓ All linters passed$(NC)"

lint-check: ## Check code formatting and style
	@echo "$(BLUE)Running linters...$(NC)"
	@echo "$(BLUE)  → black...$(NC)"
	@$(UV) run black --check $(PROJECT_ROOT)
	@echo "$(BLUE)  → ruff...$(NC)"
	@$(UV) run ruff check $(PROJECT_ROOT)
	@echo "$(GREEN)✓ Lint checks passed$(NC)"

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checking...$(NC)"
	@$(UV) run mypy $(PROJECT_ROOT)/
	@echo "$(GREEN)✓ Type checking passed$(NC)"

# Pre-commit
# ============================================================================

pre-commit: ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	$(UV) run pre-commit run --all-files
	@echo "$(GREEN)✓ Pre-commit checks passed$(NC)"

pre-commit-install: ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	$(UV) run pre-commit install
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"
