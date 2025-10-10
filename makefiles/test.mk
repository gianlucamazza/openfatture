# ============================================================================
# test.mk - Testing tasks (unit, integration, ai, payment, coverage)
# ============================================================================

.PHONY: test test-all test-unit test-integration test-ai test-payment test-services
.PHONY: test-fast test-watch test-verbose test-parallel
.PHONY: coverage coverage-report coverage-html coverage-xml
.PHONY: test-core test-sdi test-cli test-utils

# Main test targets
# ============================================================================

test: test-all ## Run all tests with coverage

test-all: ## Run complete test suite with coverage
	@echo "$(BLUE)Running all tests...$(NC)"
	$(PYTEST) tests/ -v \
		--cov=$(PROJECT_ROOT) \
		--cov-report=term-missing \
		--cov-report=html \
		--tb=short
	@echo "$(GREEN)✓ All tests passed$(NC)"

test-fast: ## Run tests without coverage (faster)
	@echo "$(BLUE)Running fast tests (no coverage)...$(NC)"
	$(PYTEST) tests/ -v --no-cov --tb=short
	@echo "$(GREEN)✓ Tests passed$(NC)"

test-verbose: ## Run tests with verbose output
	@echo "$(BLUE)Running tests with verbose output...$(NC)"
	$(PYTEST) tests/ -vv --tb=long

test-watch: ## Run tests in watch mode (requires pytest-watch)
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(NC)"
	$(UV) run ptw -- -v --tb=short

test-parallel: ## Run tests in parallel (requires pytest-xdist)
	@echo "$(BLUE)Running tests in parallel...$(NC)"
	$(PYTEST) tests/ -v -n auto --cov=$(PROJECT_ROOT) --cov-report=term-missing
	@echo "$(GREEN)✓ Parallel tests complete$(NC)"

# Module-specific tests
# ============================================================================

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	$(PYTEST) tests/unit/ -v --tb=short
	@echo "$(GREEN)✓ Unit tests passed$(NC)"

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	$(PYTEST) tests/integration/ -v --tb=short
	@echo "$(GREEN)✓ Integration tests passed$(NC)"

test-core: ## Run core module tests
	@echo "$(BLUE)Running core module tests...$(NC)"
	$(PYTEST) tests/unit/test_*_service.py tests/unit/test_batch_*.py -v
	@echo "$(GREEN)✓ Core tests passed$(NC)"

test-sdi: ## Run SDI module tests
	@echo "$(BLUE)Running SDI module tests...$(NC)"
	$(PYTEST) tests/unit/test_xml_builder.py \
		tests/unit/test_xsd_validator.py \
		tests/unit/test_pec_sender.py \
		tests/unit/test_sdi_notifiche.py \
		tests/unit/test_digital_signature.py \
		-v
	@echo "$(GREEN)✓ SDI tests passed$(NC)"

test-cli: ## Run CLI tests
	@echo "$(BLUE)Running CLI tests...$(NC)"
	$(PYTEST) tests/cli/ -v --tb=short
	@echo "$(GREEN)✓ CLI tests passed$(NC)"

test-utils: ## Run utility tests
	@echo "$(BLUE)Running utility tests...$(NC)"
	$(PYTEST) tests/unit/test_validators*.py \
		tests/unit/test_email_templates.py \
		tests/unit/test_logging.py \
		tests/unit/test_security.py \
		tests/unit/test_rate_limiter.py \
		-v
	@echo "$(GREEN)✓ Utility tests passed$(NC)"

# AI module tests
# ============================================================================

test-ai: ## Run AI module tests
	@echo "$(BLUE)Running AI module tests...$(NC)"
	$(PYTEST) tests/ai/ -v \
		--cov=$(PROJECT_ROOT)/ai \
		--cov-report=term-missing \
		--tb=short
	@echo "$(GREEN)✓ AI tests passed$(NC)"

test-ai-unit: ## Run AI unit tests only
	@echo "$(BLUE)Running AI unit tests...$(NC)"
	$(PYTEST) tests/unit/test_ai_*.py -v --tb=short
	@echo "$(GREEN)✓ AI unit tests passed$(NC)"

test-ai-integration: ## Run AI integration tests
	@echo "$(BLUE)Running AI integration tests...$(NC)"
	$(PYTEST) tests/ai/test_*_integration.py -v --tb=short
	@echo "$(GREEN)✓ AI integration tests passed$(NC)"

test-ai-streaming: ## Run AI streaming tests
	@echo "$(BLUE)Running AI streaming tests...$(NC)"
	$(PYTEST) tests/ai/test_streaming.py -v
	@echo "$(GREEN)✓ AI streaming tests passed$(NC)"

test-ai-cache: ## Run AI cache tests
	@echo "$(BLUE)Running AI cache tests...$(NC)"
	$(PYTEST) tests/ai/cache/ -v --tb=short
	@echo "$(GREEN)✓ AI cache tests passed$(NC)"

test-ai-token-counter: ## Run token counter tests
	@echo "$(BLUE)Running token counter tests...$(NC)"
	$(PYTEST) tests/ai/test_token_counter.py -v
	@echo "$(GREEN)✓ Token counter tests passed$(NC)"

# Payment module tests
# ============================================================================

test-payment: ## Run payment module tests (>85% coverage required)
	@echo "$(BLUE)Running payment module tests...$(NC)"
	$(PYTEST) tests/payment/ -v \
		--cov=$(PROJECT_ROOT)/payment \
		--cov-report=term-missing \
		--cov-fail-under=85 \
		--tb=short
	@echo "$(GREEN)✓ Payment tests passed (coverage >85%)$(NC)"

test-payment-domain: ## Run payment domain tests
	@echo "$(BLUE)Running payment domain tests...$(NC)"
	$(PYTEST) tests/payment/domain/ -v --tb=short
	@echo "$(GREEN)✓ Payment domain tests passed$(NC)"

test-payment-matchers: ## Run payment matchers tests
	@echo "$(BLUE)Running payment matchers tests...$(NC)"
	$(PYTEST) tests/payment/matchers/ -v --tb=short
	@echo "$(GREEN)✓ Payment matchers tests passed$(NC)"

# Services tests
# ============================================================================

test-services: ## Run services tests (PDF, etc.)
	@echo "$(BLUE)Running services tests...$(NC)"
	$(PYTEST) tests/services/ -v --tb=short
	@echo "$(GREEN)✓ Services tests passed$(NC)"

test-pdf: ## Run PDF generator tests
	@echo "$(BLUE)Running PDF generator tests...$(NC)"
	$(PYTEST) tests/services/test_pdf_generator.py -v
	@echo "$(GREEN)✓ PDF tests passed$(NC)"

# Coverage targets
# ============================================================================

coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(PYTEST) tests/ \
		--cov=$(PROJECT_ROOT) \
		--cov-report=term-missing \
		--cov-report=html \
		--cov-report=xml
	@echo "$(GREEN)✓ Coverage report generated$(NC)"
	@echo "$(BLUE)HTML report: $(CYAN)htmlcov/index.html$(NC)"

coverage-report: coverage ## Generate and open coverage report
	@echo "$(BLUE)Opening coverage report...$(NC)"
	@open htmlcov/index.html 2>/dev/null || xdg-open htmlcov/index.html 2>/dev/null || true

coverage-html: ## Generate HTML coverage report only
	@echo "$(BLUE)Generating HTML coverage report...$(NC)"
	$(PYTEST) tests/ --cov=$(PROJECT_ROOT) --cov-report=html
	@echo "$(GREEN)✓ HTML coverage report: $(CYAN)htmlcov/index.html$(NC)"

coverage-xml: ## Generate XML coverage report (for CI)
	@echo "$(BLUE)Generating XML coverage report...$(NC)"
	$(PYTEST) tests/ --cov=$(PROJECT_ROOT) --cov-report=xml
	@echo "$(GREEN)✓ XML coverage report: $(CYAN)coverage.xml$(NC)"

coverage-threshold: ## Check coverage meets threshold (80%)
	@echo "$(BLUE)Checking coverage threshold (80%)...$(NC)"
	$(PYTEST) tests/ \
		--cov=$(PROJECT_ROOT) \
		--cov-fail-under=80 \
		--cov-report=term-missing
	@echo "$(GREEN)✓ Coverage threshold met$(NC)"

# Test shortcuts
# ============================================================================

t: test-all ## Shortcut for test-all
tw: test-watch ## Shortcut for test-watch
tu: test-unit ## Shortcut for test-unit
ti: test-integration ## Shortcut for test-integration
ta: test-ai ## Shortcut for test-ai
tp: test-payment ## Shortcut for test-payment
