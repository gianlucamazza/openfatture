# ============================================================================
# dev.mk - Development tools and database operations
# ============================================================================

.PHONY: dev-setup dev-env dev-check db-init db-reset db-seed db-migrate db-shell
.PHONY: run run-interactive run-help run-version
.PHONY: shell ipython jupyter notebook
.PHONY: docs docs-serve docs-build docs-clean

# Development setup
# ============================================================================

dev-setup: install-dev ## Complete development environment setup
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@echo "$(BLUE)  → Installing pre-commit hooks...$(NC)"
	@$(UV) run pre-commit install
	@echo "$(BLUE)  → Creating .env file (if not exists)...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env 2>/dev/null || touch .env; \
		echo "$(YELLOW)⚠️  Please edit .env with your configuration$(NC)"; \
	else \
		echo "$(GREEN)✓ .env already exists$(NC)"; \
	fi
	@echo "$(BLUE)  → Creating data directories...$(NC)"
	@mkdir -p ~/.openfatture/data ~/.openfatture/archivio ~/.openfatture/certificates
	@echo "$(GREEN)✓ Development environment ready!$(NC)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Edit .env with your configuration"
	@echo "  2. Run: $(CYAN)make db-init$(NC)"
	@echo "  3. Run: $(CYAN)make run-interactive$(NC)"
	@echo ""

dev-env: ## Show development environment info
	@echo "$(BLUE)Development Environment:$(NC)"
	@echo "  Project: $(PROJECT_NAME)"
	@echo "  Python: $(PYTHON_VERSION)"
	@echo "  UV: $(shell $(UV) --version 2>/dev/null || echo 'not installed')"
	@echo "  Git Branch: $(shell git branch --show-current 2>/dev/null || echo 'not a git repo')"
	@echo "  Git Status: $(shell git status --porcelain 2>/dev/null | wc -l | xargs) files changed"
	@echo ""
	@echo "$(BLUE)Paths:$(NC)"
	@echo "  Project Root: $(PWD)"
	@echo "  Python: $(shell which python3 2>/dev/null || echo 'not found')"
	@echo "  Data Dir: ~/.openfatture/data"
	@echo ""

dev-check: ## Check development prerequisites
	@echo "$(BLUE)Checking prerequisites...$(NC)"
	@command -v uv >/dev/null 2>&1 && echo "$(GREEN)✓ uv$(NC)" || echo "$(RED)✗ uv not installed$(NC)"
	@command -v python3 >/dev/null 2>&1 && echo "$(GREEN)✓ python3$(NC)" || echo "$(RED)✗ python3 not installed$(NC)"
	@command -v docker >/dev/null 2>&1 && echo "$(GREEN)✓ docker$(NC)" || echo "$(YELLOW)⚠️  docker not installed (optional)$(NC)"
	@command -v git >/dev/null 2>&1 && echo "$(GREEN)✓ git$(NC)" || echo "$(RED)✗ git not installed$(NC)"
	@[ -f .env ] && echo "$(GREEN)✓ .env configured$(NC)" || echo "$(YELLOW)⚠️  .env not found$(NC)"
	@[ -d ~/.openfatture/data ] && echo "$(GREEN)✓ data directory$(NC)" || echo "$(YELLOW)⚠️  data directory not found$(NC)"

# Database operations
# ============================================================================

db-init: ## Initialize database
	@echo "$(BLUE)Initializing database...$(NC)"
	$(PYTHON) -c "from openfatture.storage.database.session import init_db; init_db()"
	@echo "$(GREEN)✓ Database initialized$(NC)"

db-reset: ## Reset database (WARNING: deletes all data!)
	@echo "$(YELLOW)⚠️  This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(BLUE)Resetting database...$(NC)"; \
		rm -f ~/.openfatture/data/openfatture.db; \
		$(MAKE) db-init; \
		echo "$(GREEN)✓ Database reset complete$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

db-seed: ## Seed database with example data
	@echo "$(BLUE)Seeding database...$(NC)"
	@if [ -f scripts/seed_database.py ]; then \
		$(PYTHON) scripts/seed_database.py; \
		echo "$(GREEN)✓ Database seeded$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Seed script not found$(NC)"; \
	fi

db-migrate: ## Run database migrations
	@echo "$(BLUE)Running migrations...$(NC)"
	@echo "$(YELLOW)⚠️  Migrations not yet implemented$(NC)"
	@echo "$(YELLOW)Future: will use Alembic for migrations$(NC)"

db-shell: ## Open database shell (SQLite)
	@echo "$(BLUE)Opening database shell...$(NC)"
	@if [ -f ~/.openfatture/data/openfatture.db ]; then \
		sqlite3 ~/.openfatture/data/openfatture.db; \
	else \
		echo "$(RED)✗ Database not found. Run: make db-init$(NC)"; \
	fi

db-backup: ## Backup database
	@echo "$(BLUE)Backing up database...$(NC)"
	@mkdir -p backups
	@if [ -f ~/.openfatture/data/openfatture.db ]; then \
		cp ~/.openfatture/data/openfatture.db backups/openfatture_$$(date +%Y%m%d_%H%M%S).db; \
		echo "$(GREEN)✓ Database backed up to backups/$(NC)"; \
	else \
		echo "$(RED)✗ Database not found$(NC)"; \
	fi

db-restore: ## Restore database from backup (usage: make db-restore BACKUP=filename)
	@if [ -z "$(BACKUP)" ]; then \
		echo "$(RED)✗ Please specify backup file: make db-restore BACKUP=filename$(NC)"; \
		echo "$(BLUE)Available backups:$(NC)"; \
		ls -lh backups/*.db 2>/dev/null || echo "  No backups found"; \
	elif [ -f "backups/$(BACKUP)" ]; then \
		echo "$(YELLOW)⚠️  This will overwrite current database!$(NC)"; \
		read -p "Continue? [y/N] " -n 1 -r; \
		echo; \
		if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
			cp backups/$(BACKUP) ~/.openfatture/data/openfatture.db; \
			echo "$(GREEN)✓ Database restored$(NC)"; \
		fi \
	else \
		echo "$(RED)✗ Backup file not found: backups/$(BACKUP)$(NC)"; \
	fi

# Run targets
# ============================================================================

run: ## Run OpenFatture CLI
	@echo "$(BLUE)Starting OpenFatture...$(NC)"
	$(UV) run openfatture --help

run-interactive: ## Run OpenFatture in interactive mode
	@echo "$(BLUE)Starting OpenFatture (interactive mode)...$(NC)"
	$(UV) run openfatture -i

run-help: ## Show OpenFatture help
	$(UV) run openfatture --help

run-version: ## Show OpenFatture version
	$(UV) run openfatture --version

run-config: ## Show OpenFatture configuration
	$(UV) run openfatture config show

run-stats: ## Show invoice statistics
	$(UV) run openfatture fattura stats

# Development shells
# ============================================================================

shell: ## Start Python shell with OpenFatture loaded
	@echo "$(BLUE)Starting Python shell...$(NC)"
	$(UV) run python -i -c "from openfatture import *; print('OpenFatture loaded. Use help() for info.')"

ipython: ## Start IPython shell
	@echo "$(BLUE)Starting IPython...$(NC)"
	$(UV) run ipython

jupyter: ## Start Jupyter notebook
	@echo "$(BLUE)Starting Jupyter notebook...$(NC)"
	$(UV) run jupyter notebook

notebook: jupyter ## Alias for jupyter

# Documentation
# ============================================================================

docs-build: ## Build documentation
	@echo "$(BLUE)Building documentation...$(NC)"
	@if [ -d docs ]; then \
		cd docs && $(MAKE) html; \
		echo "$(GREEN)✓ Documentation built$(NC)"; \
		echo "$(BLUE)Open: $(CYAN)docs/_build/html/index.html$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  docs/ directory not found$(NC)"; \
	fi

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation at http://localhost:8000$(NC)"
	@if [ -d docs/_build/html ]; then \
		cd docs/_build/html && python -m http.server 8000; \
	else \
		echo "$(RED)✗ Documentation not built. Run: make docs-build$(NC)"; \
	fi

docs-clean: ## Clean documentation build
	@echo "$(BLUE)Cleaning documentation...$(NC)"
	@if [ -d docs ]; then \
		cd docs && $(MAKE) clean; \
		echo "$(GREEN)✓ Documentation cleaned$(NC)"; \
	fi

docs: docs-build ## Alias for docs-build

# Development shortcuts
# ============================================================================

i: run-interactive ## Shortcut for run-interactive
s: shell ## Shortcut for shell
