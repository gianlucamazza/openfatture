# ============================================================================
# ai.mk - AI-specific commands and tools
# ============================================================================

.PHONY: ai-chat ai-describe ai-suggest-vat ai-forecast ai-check ai-session
.PHONY: ai-cache-info ai-cache-clear ai-providers ai-test-ollama
.PHONY: lint-ai test-ai-full

# AI Assistant commands
# ============================================================================

ai-chat: ## Start AI chat assistant
	@echo "$(BLUE)Starting AI chat assistant...$(NC)"
	@echo "$(YELLOW)Using provider from AI_PROVIDER env var (default: openai)$(NC)"
	$(UV) run openfatture ai chat

ai-describe: ## Generate invoice description (usage: make ai-describe TEXT="sviluppo API")
	@if [ -z "$(TEXT)" ]; then \
		echo "$(RED)✗ Please provide TEXT: make ai-describe TEXT='your text'$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Generating invoice description...$(NC)"
	$(UV) run openfatture ai describe "$(TEXT)"

ai-suggest-vat: ## Suggest VAT rate (usage: make ai-suggest-vat DESC="consulenza IT")
	@if [ -z "$(DESC)" ]; then \
		echo "$(RED)✗ Please provide DESC: make ai-suggest-vat DESC='description'$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Suggesting VAT rate...$(NC)"
	$(UV) run openfatture ai suggest-vat "$(DESC)"

ai-forecast: ## Generate cash flow forecast
	@echo "$(BLUE)Generating cash flow forecast...$(NC)"
	$(UV) run openfatture ai forecast

ai-check: ## Check invoice compliance
	@echo "$(BLUE)Checking invoice compliance...$(NC)"
	$(UV) run openfatture ai check

# AI Session management
# ============================================================================

ai-session-list: ## List AI chat sessions
	@echo "$(BLUE)AI Chat Sessions:$(NC)"
	$(UV) run openfatture ai session list

ai-session-show: ## Show session details (usage: make ai-session-show ID=session_id)
	@if [ -z "$(ID)" ]; then \
		echo "$(RED)✗ Please provide session ID: make ai-session-show ID=xxx$(NC)"; \
		exit 1; \
	fi
	$(UV) run openfatture ai session show $(ID)

ai-session-export: ## Export session (usage: make ai-session-export ID=session_id FORMAT=json)
	@if [ -z "$(ID)" ]; then \
		echo "$(RED)✗ Please provide session ID: make ai-session-export ID=xxx$(NC)"; \
		exit 1; \
	fi
	@FORMAT=$${FORMAT:-json}; \
	echo "$(BLUE)Exporting session to $$FORMAT...$(NC)"; \
	$(UV) run openfatture ai session export $(ID) --format $$FORMAT

ai-session-clear: ## Clear old sessions
	@echo "$(YELLOW)⚠️  This will delete old chat sessions$(NC)"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(UV) run openfatture ai session clear; \
		echo "$(GREEN)✓ Sessions cleared$(NC)"; \
	fi

# AI Cache management
# ============================================================================

ai-cache-info: ## Show AI cache statistics
	@echo "$(BLUE)AI Cache Statistics:$(NC)"
	@echo "$(YELLOW)Cache location: ~/.openfatture/cache/$(NC)"
	@if [ -d ~/.openfatture/cache ]; then \
		echo "Cache size: $$(du -sh ~/.openfatture/cache 2>/dev/null | cut -f1)"; \
		echo "Files: $$(find ~/.openfatture/cache -type f 2>/dev/null | wc -l | xargs)"; \
	else \
		echo "$(YELLOW)No cache found$(NC)"; \
	fi

ai-cache-clear: ## Clear AI cache
	@echo "$(YELLOW)⚠️  This will clear the AI response cache$(NC)"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf ~/.openfatture/cache/; \
		echo "$(GREEN)✓ Cache cleared$(NC)"; \
	fi

ai-cache-warmup: ## Warm up AI cache with common prompts
	@echo "$(BLUE)Warming up AI cache...$(NC)"
	@echo "$(YELLOW)⚠️  Not yet implemented$(NC)"

# AI Providers
# ============================================================================

ai-providers: ## List available AI providers
	@echo "$(BLUE)Available AI Providers:$(NC)"
	@echo ""
	@echo "$(CYAN)1. OpenAI$(NC) (default)"
	@echo "   Models: gpt-4o, gpt-4-turbo, gpt-3.5-turbo"
	@echo "   Config: OPENAI_API_KEY"
	@echo ""
	@echo "$(CYAN)2. Anthropic$(NC)"
	@echo "   Models: claude-3-opus, claude-3-sonnet, claude-3-haiku"
	@echo "   Config: ANTHROPIC_API_KEY"
	@echo ""
	@echo "$(CYAN)3. Ollama$(NC) (local)"
	@echo "   Models: llama3.2, mistral, codellama"
	@echo "   Config: OLLAMA_BASE_URL (default: http://localhost:11434)"
	@echo ""
	@echo "$(YELLOW)Set provider with: export AI_PROVIDER=openai|anthropic|ollama$(NC)"

ai-test-openai: ## Test OpenAI connection
	@echo "$(BLUE)Testing OpenAI connection...$(NC)"
	@if [ -z "$$OPENAI_API_KEY" ]; then \
		echo "$(RED)✗ OPENAI_API_KEY not set$(NC)"; \
		exit 1; \
	fi
	@$(PYTHON) -c "from openfatture.ai.providers.openai import OpenAIProvider; \
		p = OpenAIProvider(); \
		print('✓ OpenAI connection OK')"

ai-test-anthropic: ## Test Anthropic connection
	@echo "$(BLUE)Testing Anthropic connection...$(NC)"
	@if [ -z "$$ANTHROPIC_API_KEY" ]; then \
		echo "$(RED)✗ ANTHROPIC_API_KEY not set$(NC)"; \
		exit 1; \
	fi
	@$(PYTHON) -c "from openfatture.ai.providers.anthropic import AnthropicProvider; \
		p = AnthropicProvider(); \
		print('✓ Anthropic connection OK')"

ai-test-ollama: ## Test Ollama connection
	@echo "$(BLUE)Testing Ollama connection...$(NC)"
	@if [ -f scripts/check_ollama.sh ]; then \
		./scripts/check_ollama.sh; \
	else \
		curl -s http://localhost:11434/api/tags >/dev/null && \
		echo "$(GREEN)✓ Ollama is running$(NC)" || \
		echo "$(RED)✗ Ollama not running. Start with: ollama serve$(NC)"; \
	fi

ai-setup-ollama: ## Setup Ollama with recommended models
	@echo "$(BLUE)Setting up Ollama...$(NC)"
	@echo "$(YELLOW)This will download llama3.2 (~2GB)$(NC)"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		ollama pull llama3.2; \
		echo "$(GREEN)✓ Ollama setup complete$(NC)"; \
	fi

# AI Development
# ============================================================================

lint-ai: ## Lint AI module only
	@echo "$(BLUE)Linting AI module...$(NC)"
	$(UV) run black --check $(PROJECT_ROOT)/ai/
	$(UV) run ruff check $(PROJECT_ROOT)/ai/
	$(UV) run mypy $(PROJECT_ROOT)/ai/
	@echo "$(GREEN)✓ AI module lint passed$(NC)"

test-ai-full: ## Run complete AI test suite
	@echo "$(BLUE)Running complete AI test suite...$(NC)"
	@echo "$(BLUE)  → Unit tests...$(NC)"
	@$(PYTEST) tests/unit/test_ai_*.py -v
	@echo "$(BLUE)  → Integration tests...$(NC)"
	@$(PYTEST) tests/ai/test_*_integration.py -v
	@echo "$(BLUE)  → Streaming tests...$(NC)"
	@$(PYTEST) tests/ai/test_streaming.py -v
	@echo "$(BLUE)  → Cache tests...$(NC)"
	@$(PYTEST) tests/ai/cache/ -v
	@echo "$(BLUE)  → Token counter tests...$(NC)"
	@$(PYTEST) tests/ai/test_token_counter.py -v
	@echo "$(GREEN)✓ All AI tests passed$(NC)"

ai-benchmark: ## Run AI performance benchmarks
	@echo "$(BLUE)Running AI benchmarks...$(NC)"
	@echo "$(YELLOW)⚠️  Not yet implemented$(NC)"
	@echo "$(YELLOW)Future: will benchmark all providers$(NC)"

# AI Interactive demos
# ============================================================================

ai-demo-chat: ## Run AI chat demo
	@echo "$(BLUE)Starting AI chat demo...$(NC)"
	@if [ -f examples/ai_chat_demo.py ]; then \
		$(PYTHON) examples/ai_chat_demo.py; \
	else \
		echo "$(YELLOW)Demo not found, starting regular chat...$(NC)"; \
		$(MAKE) ai-chat; \
	fi

ai-demo-invoice: ## Run AI invoice assistant demo
	@echo "$(BLUE)Starting AI invoice assistant demo...$(NC)"
	@if [ -f examples/ai_invoice_assistant.py ]; then \
		$(PYTHON) examples/ai_invoice_assistant.py; \
	else \
		echo "$(RED)✗ Demo file not found: examples/ai_invoice_assistant.py$(NC)"; \
	fi

# AI Shortcuts
# ============================================================================

chat: ai-chat ## Shortcut for ai-chat
forecast: ai-forecast ## Shortcut for ai-forecast
