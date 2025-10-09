# OpenFatture - Makefile for Common Development Tasks
# Requirements: make, poetry
#
# Usage:
#   make install    - Install dependencies
#   make test       - Run tests
#   make lint       - Run linters
#   make format     - Format code
#   make run        - Run CLI
#   make docker     - Build and run Docker container
#   make clean      - Clean cache and temp files

.PHONY: help install test lint format coverage run clean docker docker-build docker-run

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "$(BLUE)OpenFatture - Development Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

install: ## Install dependencies with Poetry
	@echo "$(BLUE)Installing dependencies...$(NC)"
	poetry install --with dev
	poetry run pre-commit install
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-prod: ## Install production dependencies only
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	poetry install --without dev
	@echo "$(GREEN)✓ Production dependencies installed$(NC)"

test: ## Run tests with pytest
	@echo "$(BLUE)Running tests...$(NC)"
	poetry run pytest -v

test-fast: ## Run tests without coverage (faster)
	@echo "$(BLUE)Running fast tests...$(NC)"
	poetry run pytest -v --no-cov

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	poetry run ptw -- -v

coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	poetry run pytest --cov=openfatture --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/$(NC)"

lint: ## Run all linters (black, ruff, mypy)
	@echo "$(BLUE)Running linters...$(NC)"
	poetry run black --check .
	poetry run ruff check .
	poetry run mypy openfatture/
	@echo "$(GREEN)✓ All linters passed$(NC)"

format: ## Format code with black and ruff
	@echo "$(BLUE)Formatting code...$(NC)"
	poetry run black .
	poetry run ruff check --fix .
	@echo "$(GREEN)✓ Code formatted$(NC)"

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Type checking...$(NC)"
	poetry run mypy openfatture/

run: ## Run OpenFatture CLI
	@echo "$(BLUE)Starting OpenFatture...$(NC)"
	poetry run openfatture --help

init: ## Initialize OpenFatture (run setup)
	@echo "$(BLUE)Initializing OpenFatture...$(NC)"
	poetry run openfatture init

clean: ## Clean cache, temp files, and build artifacts
	@echo "$(BLUE)Cleaning...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ htmlcov/ .coverage
	@echo "$(GREEN)✓ Cleaned$(NC)"

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t openfatture:latest .
	@echo "$(GREEN)✓ Docker image built$(NC)"

docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	docker run -it --rm \
		-v $(PWD)/.env:/app/.env \
		-v $(PWD)/data:/root/.openfatture/data \
		openfatture:latest

docker: docker-build docker-run ## Build and run Docker container

docker-compose-up: ## Start services with docker-compose
	@echo "$(BLUE)Starting services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Services started$(NC)"

docker-compose-down: ## Stop services with docker-compose
	@echo "$(BLUE)Stopping services...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

pre-commit: ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	poetry run pre-commit run --all-files

security: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	poetry run bandit -r openfatture/ -ll
	poetry run safety check
	@echo "$(GREEN)✓ Security checks passed$(NC)"

docs: ## Build documentation
	@echo "$(BLUE)Building documentation...$(NC)"
	cd docs && poetry run make html
	@echo "$(GREEN)✓ Documentation built in docs/_build/html/$(NC)"

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation at http://localhost:8000$(NC)"
	cd docs/_build/html && python -m http.server 8000

bump-version: ## Bump version (usage: make bump-version VERSION=0.2.0)
	@echo "$(BLUE)Bumping version to $(VERSION)...$(NC)"
	poetry version $(VERSION)
	@echo "$(GREEN)✓ Version bumped to $(VERSION)$(NC)"

publish: ## Publish package to PyPI
	@echo "$(BLUE)Publishing to PyPI...$(NC)"
	poetry build
	poetry publish
	@echo "$(GREEN)✓ Published to PyPI$(NC)"

dev-setup: install ## Complete development environment setup
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@echo "$(YELLOW)Creating .env from example...$(NC)"
	cp -n .env.example .env || true
	@echo "$(GREEN)✓ Development environment ready!$(NC)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Edit .env with your configuration"
	@echo "  2. Run: make init"
	@echo "  3. Run: make test"
	@echo ""

ci: format lint test ## Run CI checks (format, lint, test)
	@echo "$(GREEN)✓ All CI checks passed$(NC)"

all: clean install format lint test ## Run full setup and checks
	@echo "$(GREEN)✓ All tasks completed$(NC)"

# Alias commands for convenience
t: test
f: format
l: lint
r: run
c: clean
