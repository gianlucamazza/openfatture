# OpenFatture - Makefile for Common Development Tasks
# Requirements: make, uv

SHELL := /bin/bash

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
CYAN := \033[0;36m
RED := \033[0;31m
NC := \033[0m # No Color

# Tooling configuration
UV ?= uv
PYTHON ?= python3

PROJECT_NAME := openfatture
PROJECT_ROOT := openfatture
PYTHON_VERSION := $(shell if [ -f .python-version ]; then cat .python-version; else $(PYTHON) -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"; fi)
PYTEST ?= $(UV) run python -m pytest

export UV PYTHON PROJECT_NAME PROJECT_ROOT PYTHON_VERSION PYTEST

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@echo "$(BLUE)OpenFatture - Development Commands$(NC)"
	@echo ""
	@grep -Eh '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort -u | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

MAKEFILES_DIR := makefiles

include $(MAKEFILES_DIR)/base.mk
include $(MAKEFILES_DIR)/test.mk
include $(MAKEFILES_DIR)/dev.mk
include $(MAKEFILES_DIR)/docker.mk
include $(MAKEFILES_DIR)/ci.mk
include $(MAKEFILES_DIR)/ai.mk
include $(MAKEFILES_DIR)/media.mk

.PHONY: web-install
web-install: ## Install web UI dependencies
	@echo "$(CYAN)Installing web UI dependencies...$(NC)"
	uv sync --extra web

.PHONY: web-run
web-run: ## Run web UI in development mode
	@echo "$(CYAN)Starting web UI...$(NC)"
	uv run streamlit run $(PROJECT_ROOT)/web/app.py

.PHONY: web-run-prod
web-run-prod: ## Run web UI in production mode
	@echo "$(CYAN)Starting web UI in production mode...$(NC)"
	uv run streamlit run $(PROJECT_ROOT)/web/app.py \
		--server.address 0.0.0.0 \
		--server.port 8501 \
		--server.fileWatcherType none \
		--browser.gatherUsageStats false

.PHONY: web-test
web-test: ## Run web UI tests
	@echo "$(CYAN)Running web UI tests...$(NC)"
	uv run python -m pytest tests/web/ -v

.PHONY: web
web: web-install web-run ## Install and run web UI

.PHONY: docker
docker: docker-build docker-run ## Build and run Docker container
