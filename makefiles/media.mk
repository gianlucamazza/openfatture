# ============================================================================
# media.mk - Media automation (VHS videos, screenshots, demos)
# ============================================================================

.PHONY: media-install media-check media-reset media-clean
.PHONY: media-scenarioA media-scenarioB media-scenarioC media-scenarioD media-scenarioE
.PHONY: media-all media-screenshots media-optimize
.PHONY: media-test media-ci media-ci-scenario media-list
.PHONY: media-template media-template-A media-template-B media-template-C media-template-D media-template-E
.PHONY: media-templates media-template-check

# Media directories
MEDIA_DIR := media
MEDIA_OUTPUT := $(MEDIA_DIR)/output
MEDIA_SCREENSHOTS := $(MEDIA_DIR)/screenshots/v2025
MEDIA_AUTOMATION := $(MEDIA_DIR)/automation

# Prerequisites
# ============================================================================

media-install: ## Install media automation tools (VHS, ffmpeg)
	@echo "$(BLUE)Installing media automation tools...$(NC)"
	@echo "$(BLUE)  → Checking VHS...$(NC)"
	@command -v vhs >/dev/null 2>&1 || \
		(echo "$(YELLOW)Installing VHS...$(NC)" && brew install charmbracelet/tap/vhs)
	@echo "$(BLUE)  → Checking ffmpeg...$(NC)"
	@command -v ffmpeg >/dev/null 2>&1 || \
		(echo "$(YELLOW)Installing ffmpeg...$(NC)" && brew install ffmpeg)
	@echo "$(BLUE)  → Checking Ollama...$(NC)"
	@command -v ollama >/dev/null 2>&1 || \
		echo "$(YELLOW)⚠️  Ollama not found. Install from https://ollama.com/download$(NC)"
	@echo "$(GREEN)✓ Media tools installed$(NC)"

media-check: ## Check prerequisites for media generation
	@echo "$(BLUE)Checking media prerequisites...$(NC)"
	@command -v vhs >/dev/null 2>&1 && echo "$(GREEN)✓ VHS$(NC)" || echo "$(RED)✗ VHS not installed$(NC)"
	@command -v ffmpeg >/dev/null 2>&1 && echo "$(GREEN)✓ ffmpeg$(NC)" || echo "$(RED)✗ ffmpeg not installed$(NC)"
	@command -v ollama >/dev/null 2>&1 && echo "$(GREEN)✓ Ollama$(NC)" || echo "$(YELLOW)⚠️  Ollama not installed (needed for AI scenario)$(NC)"
	@[ -d $(MEDIA_AUTOMATION) ] && echo "$(GREEN)✓ Automation scripts$(NC)" || echo "$(RED)✗ Automation directory not found$(NC)"
	@if [ -f scripts/check_ollama.sh ]; then \
		echo "$(BLUE)Checking Ollama models...$(NC)"; \
		./scripts/check_ollama.sh llama3.2 || echo "$(YELLOW)⚠️  llama3.2 not available$(NC)"; \
	fi
	@echo "$(GREEN)✓ Prerequisites checked$(NC)"

media-reset: ## Reset demo environment
	@echo "$(BLUE)Resetting demo environment...$(NC)"
	@if [ -f scripts/reset_demo.sh ]; then \
		./scripts/reset_demo.sh; \
		echo "$(GREEN)✓ Demo environment ready$(NC)"; \
	elif [ -f scripts/reset_demo.py ]; then \
		$(PYTHON) scripts/reset_demo.py; \
		echo "$(GREEN)✓ Demo environment ready$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Reset script not found$(NC)"; \
	fi

# Video generation (VHS)
# ============================================================================

media-scenarioA: media-check media-reset ## Generate Scenario A video (Onboarding)
	@echo "$(BLUE)Generating Scenario A: Onboarding...$(NC)"
	@if [ -f $(MEDIA_AUTOMATION)/scenario_a_onboarding.tape ]; then \
		vhs $(MEDIA_AUTOMATION)/scenario_a_onboarding.tape; \
		echo "$(GREEN)✓ Scenario A: $(CYAN)$(MEDIA_OUTPUT)/scenario_a_onboarding.mp4$(NC)"; \
	else \
		echo "$(RED)✗ Tape file not found: $(MEDIA_AUTOMATION)/scenario_a_onboarding.tape$(NC)"; \
	fi

media-scenarioB: media-check media-reset ## Generate Scenario B video (Invoice Creation)
	@echo "$(BLUE)Generating Scenario B: Invoice Creation...$(NC)"
	@if [ -f $(MEDIA_AUTOMATION)/scenario_b_invoice.tape ]; then \
		vhs $(MEDIA_AUTOMATION)/scenario_b_invoice.tape; \
		echo "$(GREEN)✓ Scenario B: $(CYAN)$(MEDIA_OUTPUT)/scenario_b_invoice.mp4$(NC)"; \
	else \
		echo "$(RED)✗ Tape file not found: $(MEDIA_AUTOMATION)/scenario_b_invoice.tape$(NC)"; \
	fi

media-scenarioC: media-check media-reset ## Generate Scenario C video (AI Assistant with Ollama)
	@echo "$(BLUE)Generating Scenario C: AI Assistant...$(NC)"
	@echo "$(YELLOW)⚠️  This requires Ollama with llama3.2 model$(NC)"
	@if [ -f $(MEDIA_AUTOMATION)/scenario_c_ai.tape ]; then \
		vhs $(MEDIA_AUTOMATION)/scenario_c_ai.tape; \
		echo "$(GREEN)✓ Scenario C: $(CYAN)$(MEDIA_OUTPUT)/scenario_c_ai.mp4$(NC)"; \
	else \
		echo "$(RED)✗ Tape file not found: $(MEDIA_AUTOMATION)/scenario_c_ai.tape$(NC)"; \
	fi

media-scenarioD: media-check media-reset ## Generate Scenario D video (Batch Operations)
	@echo "$(BLUE)Generating Scenario D: Batch Operations...$(NC)"
	@if [ -f $(MEDIA_AUTOMATION)/scenario_d_batch.tape ]; then \
		vhs $(MEDIA_AUTOMATION)/scenario_d_batch.tape; \
		echo "$(GREEN)✓ Scenario D: $(CYAN)$(MEDIA_OUTPUT)/scenario_d_batch.mp4$(NC)"; \
	else \
		echo "$(RED)✗ Tape file not found: $(MEDIA_AUTOMATION)/scenario_d_batch.tape$(NC)"; \
	fi

media-scenarioE: media-check media-reset ## Generate Scenario E video (PEC Integration)
	@echo "$(BLUE)Generating Scenario E: PEC Integration...$(NC)"
	@if [ -f $(MEDIA_AUTOMATION)/scenario_e_pec.tape ]; then \
		vhs $(MEDIA_AUTOMATION)/scenario_e_pec.tape; \
		echo "$(GREEN)✓ Scenario E: $(CYAN)$(MEDIA_OUTPUT)/scenario_e_pec.mp4$(NC)"; \
	else \
		echo "$(RED)✗ Tape file not found: $(MEDIA_AUTOMATION)/scenario_e_pec.tape$(NC)"; \
	fi

media-all: media-scenarioA media-scenarioB media-scenarioC media-scenarioD media-scenarioE ## Generate all scenario videos
	@echo "$(GREEN)✓ All scenario videos generated!$(NC)"
	@echo "$(BLUE)Output files:$(NC)"
	@ls -lh $(MEDIA_OUTPUT)/*.mp4 2>/dev/null || echo "No videos found"

# Screenshot capture
# ============================================================================

media-screenshots: media-check media-reset ## Capture screenshots for all scenarios
	@echo "$(BLUE)Capturing screenshots...$(NC)"
	@if [ -f scripts/capture_screenshots.py ]; then \
		$(PYTHON) scripts/capture_screenshots.py --all; \
		echo "$(GREEN)✓ Screenshots saved to $(CYAN)$(MEDIA_SCREENSHOTS)/$(NC)"; \
	else \
		echo "$(RED)✗ Screenshot script not found: scripts/capture_screenshots.py$(NC)"; \
	fi

media-screenshots-scenario: ## Capture screenshots for specific scenario (usage: make media-screenshots-scenario SCENARIO=A)
	@if [ -z "$(SCENARIO)" ]; then \
		echo "$(RED)✗ Please specify SCENARIO: make media-screenshots-scenario SCENARIO=A$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Capturing screenshots for Scenario $(SCENARIO)...$(NC)"
	@if [ -f scripts/capture_screenshots.py ]; then \
		$(PYTHON) scripts/capture_screenshots.py --scenario $(SCENARIO); \
		echo "$(GREEN)✓ Screenshots saved$(NC)"; \
	else \
		echo "$(RED)✗ Screenshot script not found$(NC)"; \
	fi

# Video optimization
# ============================================================================

media-optimize: ## Optimize video files (reduce size)
	@echo "$(BLUE)Optimizing videos...$(NC)"
	@if [ -f scripts/optimize_videos.sh ]; then \
		./scripts/optimize_videos.sh; \
		echo "$(GREEN)✓ Videos optimized$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  Optimization script not found$(NC)"; \
		echo "$(YELLOW)Manual optimization: ffmpeg -i input.mp4 -vcodec libx264 -crf 28 output.mp4$(NC)"; \
	fi

media-optimize-file: ## Optimize single video file (usage: make media-optimize-file FILE=video.mp4)
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)✗ Please specify FILE: make media-optimize-file FILE=video.mp4$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Optimizing $(FILE)...$(NC)"
	@ffmpeg -i "$(FILE)" -vcodec libx264 -crf 28 "$(FILE).optimized.mp4"
	@echo "$(GREEN)✓ Optimized: $(FILE).optimized.mp4$(NC)"

# Media conversion
# ============================================================================

media-to-gif: ## Convert video to GIF (usage: make media-to-gif FILE=video.mp4)
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)✗ Please specify FILE: make media-to-gif FILE=video.mp4$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Converting to GIF...$(NC)"
	@ffmpeg -i "$(FILE)" -vf "fps=10,scale=720:-1:flags=lanczos" -c:v gif "$(FILE).gif"
	@echo "$(GREEN)✓ GIF created: $(FILE).gif$(NC)"

media-to-webm: ## Convert video to WebM (usage: make media-to-webm FILE=video.mp4)
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)✗ Please specify FILE: make media-to-webm FILE=video.mp4$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Converting to WebM...$(NC)"
	@ffmpeg -i "$(FILE)" -c:v libvpx-vp9 -crf 30 -b:v 0 "$(FILE).webm"
	@echo "$(GREEN)✓ WebM created: $(FILE).webm$(NC)"

# Media testing
# ============================================================================

media-test: ## Test media automation (dry run)
	@echo "$(BLUE)Testing media automation...$(NC)"
	@echo "$(BLUE)  → Checking VHS tape files...$(NC)"
	@ls -1 $(MEDIA_AUTOMATION)/*.tape 2>/dev/null || echo "$(RED)No tape files found$(NC)"
	@echo "$(BLUE)  → Checking output directory...$(NC)"
	@[ -d $(MEDIA_OUTPUT) ] && echo "$(GREEN)✓ Output directory exists$(NC)" || \
		(mkdir -p $(MEDIA_OUTPUT) && echo "$(GREEN)✓ Output directory created$(NC)")
	@echo "$(BLUE)  → Checking demo data...$(NC)"
	@[ -f examples/demo/batch_import_example.csv ] && \
		echo "$(GREEN)✓ Demo data found$(NC)" || \
		echo "$(YELLOW)⚠️  Demo data not found$(NC)"
	@echo "$(GREEN)✓ Media automation test complete$(NC)"

# CI/CD simulation
# ============================================================================

media-ci: ## Simulate CI environment locally (uses Anthropic like GitHub Actions)
	@echo "$(BLUE)╔════════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║            Simulating CI Media Generation Workflow            ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(CYAN)Step 1: Check prerequisites$(NC)"
	@command -v vhs >/dev/null 2>&1 || (echo "$(RED)✗ VHS not installed$(NC)" && exit 1)
	@command -v ffmpeg >/dev/null 2>&1 || (echo "$(RED)✗ ffmpeg not installed$(NC)" && exit 1)
	@command -v uv >/dev/null 2>&1 || (echo "$(RED)✗ uv not installed$(NC)" && exit 1)
	@echo "$(GREEN)✓ Prerequisites OK$(NC)"
	@echo ""
	@echo "$(CYAN)Step 2: Verify Anthropic configuration$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(RED)✗ .env file not found$(NC)"; \
		echo "$(YELLOW)  Create .env with:$(NC)"; \
		echo "$(YELLOW)    AI_PROVIDER=anthropic$(NC)"; \
		echo "$(YELLOW)    AI_MODEL=claude-sonnet-4-5$(NC)"; \
		echo "$(YELLOW)    OPENFATTURE_AI_ANTHROPIC_API_KEY=sk-ant-...$(NC)"; \
		exit 1; \
	fi
	@grep -q "^AI_PROVIDER=anthropic" .env && echo "$(GREEN)✓ AI Provider: anthropic$(NC)" || \
		(echo "$(RED)✗ AI_PROVIDER not set to anthropic in .env$(NC)" && exit 1)
	@grep -q "^OPENFATTURE_AI_ANTHROPIC_API_KEY=" .env && echo "$(GREEN)✓ Anthropic API key configured$(NC)" || \
		(echo "$(RED)✗ OPENFATTURE_AI_ANTHROPIC_API_KEY not set in .env$(NC)" && exit 1)
	@$(PYTHON) -c "\
		from openfatture.ai.config.settings import get_ai_settings; \
		settings = get_ai_settings(); \
		print(f'$(GREEN)✓ Model: {settings.anthropic_model}$(NC)'); \
		assert settings.provider == 'anthropic', 'Provider must be anthropic'; \
		assert settings.is_provider_configured(), 'Anthropic not configured'; \
	" 2>&1 || (echo "$(RED)✗ Anthropic configuration invalid$(NC)" && exit 1)
	@echo ""
	@echo "$(CYAN)Step 3: Reset demo environment$(NC)"
	@$(MAKE) -s media-reset
	@echo ""
	@echo "$(CYAN)Step 4: Generate videos (all scenarios)$(NC)"
	@$(MAKE) -s media-all
	@echo ""
	@echo "$(CYAN)Step 5: List generated videos$(NC)"
	@ls -lh $(MEDIA_OUTPUT)/*.mp4 | awk '{printf "  %s (%s)\n", $$9, $$5}'
	@echo ""
	@du -ch $(MEDIA_OUTPUT)/*.mp4 | grep total | awk '{printf "$(CYAN)Total size: %s$(NC)\n", $$1}'
	@echo ""
	@echo "$(GREEN)╔════════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║              CI Simulation Completed Successfully              ║$(NC)"
	@echo "$(GREEN)╚════════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "  • Run $(CYAN)make media-optimize$(NC) to create HD/SD/Mobile versions"
	@echo "  • View videos in $(CYAN)media/output/$(NC)"
	@echo "  • Push changes to trigger GitHub Actions workflow"
	@echo ""

media-ci-scenario: ## Simulate CI for specific scenario (usage: make media-ci-scenario SCENARIO=A)
	@if [ -z "$(SCENARIO)" ]; then \
		echo "$(RED)✗ Please specify SCENARIO: make media-ci-scenario SCENARIO=A$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Simulating CI for Scenario $(SCENARIO)...$(NC)"
	@echo ""
	@echo "$(CYAN)Checking Anthropic configuration...$(NC)"
	@grep -q "^AI_PROVIDER=anthropic" .env && echo "$(GREEN)✓ Anthropic configured$(NC)" || \
		(echo "$(RED)✗ Anthropic not configured in .env$(NC)" && exit 1)
	@echo ""
	@echo "$(CYAN)Resetting demo environment...$(NC)"
	@$(MAKE) -s media-reset
	@echo ""
	@echo "$(CYAN)Generating Scenario $(SCENARIO)...$(NC)"
	@$(MAKE) -s media-scenario$(SCENARIO)
	@echo ""
	@echo "$(GREEN)✓ CI simulation for Scenario $(SCENARIO) complete$(NC)"

media-list: ## List all media files
	@echo "$(BLUE)Media Files:$(NC)"
	@echo ""
	@echo "$(CYAN)Videos ($(MEDIA_OUTPUT)):$(NC)"
	@ls -lh $(MEDIA_OUTPUT)/*.mp4 2>/dev/null || echo "  No videos"
	@echo ""
	@echo "$(CYAN)GIFs ($(MEDIA_OUTPUT)):$(NC)"
	@ls -lh $(MEDIA_OUTPUT)/*.gif 2>/dev/null || echo "  No GIFs"
	@echo ""
	@echo "$(CYAN)Screenshots ($(MEDIA_SCREENSHOTS)):$(NC)"
	@ls -1 $(MEDIA_SCREENSHOTS)/*.png 2>/dev/null | wc -l | xargs echo "  Total:"
	@echo ""
	@echo "$(CYAN)VHS Tapes ($(MEDIA_AUTOMATION)):$(NC)"
	@ls -1 $(MEDIA_AUTOMATION)/*.tape 2>/dev/null | wc -l | xargs echo "  Total:"
	@echo ""
	@echo "$(CYAN)Template Info:$(NC)"
	@echo "  Templates: $$(ls -1 $(MEDIA_AUTOMATION)/templates/scenarios/*.tape.j2 2>/dev/null | wc -l) scenarios"
	@echo "  Components: $$(ls -1 $(MEDIA_AUTOMATION)/templates/components/*.tapeinc 2>/dev/null | wc -l) reusable"

media-info: ## Show media file information
	@echo "$(BLUE)Media Information:$(NC)"
	@echo ""
	@if [ -d $(MEDIA_OUTPUT) ]; then \
		echo "$(CYAN)Total size:$(NC) $$(du -sh $(MEDIA_OUTPUT) 2>/dev/null | cut -f1)"; \
		echo "$(CYAN)Video count:$(NC) $$(ls -1 $(MEDIA_OUTPUT)/*.mp4 2>/dev/null | wc -l | xargs)"; \
		echo "$(CYAN)GIF count:$(NC) $$(ls -1 $(MEDIA_OUTPUT)/*.gif 2>/dev/null | wc -l | xargs)"; \
	fi
	@if [ -d $(MEDIA_SCREENSHOTS) ]; then \
		echo "$(CYAN)Screenshot count:$(NC) $$(ls -1 $(MEDIA_SCREENSHOTS)/*.png 2>/dev/null | wc -l | xargs)"; \
	fi

# Cleanup
# ============================================================================

# Template-based generation
# ============================================================================

media-template: ## Generate VHS tape from template (usage: make media-template SCENARIO=A)
	@if [ -z "$(SCENARIO)" ]; then \
		echo "$(RED)✗ Please specify SCENARIO: make media-template SCENARIO=A$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Generating template for scenario $(SCENARIO)...$(NC)"
	@if command -v uv >/dev/null 2>&1; then \
		uv run openfatture media template generate --scenario $(SCENARIO); \
		echo "$(GREEN)✓ Template generated for scenario $(SCENARIO)$(NC)"; \
	else \
		echo "$(YELLOW)⚠️  uv not found, using direct python$(NC)"; \
		python media/automation/templates/base_template.py generate --scenario $(SCENARIO); \
		echo "$(GREEN)✓ Template generated for scenario $(SCENARIO)$(NC)"; \
	fi

media-template-A: ## Generate VHS tape for Scenario A using template
	@echo "$(BLUE)Generating Scenario A template...$(NC)"
	@if command -v uv >/dev/null 2>&1; then \
		uv run openfatture media template generate --scenario A; \
	else \
		python media/automation/templates/base_template.py generate --scenario A; \
	fi
	@echo "$(GREEN)✓ Scenario A template generated$(NC)"

media-template-B: ## Generate VHS tape for Scenario B using template
	@echo "$(BLUE)Generating Scenario B template...$(NC)"
	@if command -v uv >/dev/null 2>&1; then \
		uv run openfatture media template generate --scenario B; \
	else \
		python media/automation/templates/base_template.py generate --scenario B; \
	fi
	@echo "$(GREEN)✓ Scenario B template generated$(NC)"

media-template-C: ## Generate VHS tape for Scenario C using template
	@echo "$(BLUE)Generating Scenario C template...$(NC)"
	@if command -v uv >/dev/null 2>&1; then \
		uv run openfatture media template generate --scenario C; \
	else \
		python media/automation/templates/base_template.py generate --scenario C; \
	fi
	@echo "$(GREEN)✓ Scenario C template generated$(NC)"

media-template-D: ## Generate VHS tape for Scenario D using template
	@echo "$(BLUE)Generating Scenario D template...$(NC)"
	@if command -v uv >/dev/null 2>&1; then \
		uv run openfatture media template generate --scenario D; \
	else \
		python media/automation/templates/base_template.py generate --scenario D; \
	fi
	@echo "$(GREEN)✓ Scenario D template generated$(NC)"

media-template-E: ## Generate VHS tape for Scenario E using template
	@echo "$(BLUE)Generating Scenario E template...$(NC)"
	@if command -v uv >/dev/null 2>&1; then \
		uv run openfatture media template generate --scenario E; \
	else \
		python media/automation/templates/base_template.py generate --scenario E; \
	fi
	@echo "$(GREEN)✓ Scenario E template generated$(NC)"

media-templates: ## Generate all VHS tapes from templates
	@echo "$(BLUE)Generating all scenario templates...$(NC)"
	@for s in A B C D E; do \
		echo "$(BLUE)  → Generating scenario $$s...$(NC)"; \
		if command -v uv >/dev/null 2>&1; then \
			uv run openfatture media template generate --scenario $$s; \
		else \
			python media/automation/templates/base_template.py generate --scenario $$s; \
		fi; \
	done
	@echo "$(GREEN)✓ All scenario templates generated$(NC)"

media-template-check: ## Validate all VHS templates
	@echo "$(BLUE)Validating all VHS templates...$(NC)"
	@for s in A B C D E; do \
		echo "$(BLUE)  → Validating scenario $$s...$(NC)"; \
		if command -v uv >/dev/null 2>&1; then \
			if uv run openfatture media template validate --scenario $$s; then \
				echo "$(GREEN)    ✓ Scenario $$s valid$(NC)"; \
			else \
				echo "$(RED)    ✗ Scenario $$s invalid$(NC)"; \
				exit 1; \
			fi; \
		else \
			if python media/automation/templates/base_template.py validate --scenario $$s; then \
				echo "$(GREEN)    ✓ Scenario $$s valid$(NC)"; \
			else \
				echo "$(RED)    ✗ Scenario $$s invalid$(NC)"; \
				exit 1; \
			fi; \
		fi; \
	done
	@echo "$(GREEN)✓ All templates validated$(NC)"

media-clean: ## Clean media output files
	@echo "$(YELLOW)⚠️  This will delete all generated media files!$(NC)"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(BLUE)Cleaning media output...$(NC)"; \
		rm -f $(MEDIA_OUTPUT)/*.mp4 2>/dev/null || true; \
		rm -f $(MEDIA_OUTPUT)/*.gif 2>/dev/null || true; \
		rm -f $(MEDIA_OUTPUT)/*.webm 2>/dev/null || true; \
		rm -f $(MEDIA_SCREENSHOTS)/*.txt 2>/dev/null || true; \
		rm -f $(MEDIA_SCREENSHOTS)/*.json 2>/dev/null || true; \
		echo "$(GREEN)✓ Media output cleaned$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

media-clean-cache: ## Clean VHS cache
	@echo "$(BLUE)Cleaning VHS cache...$(NC)"
	@rm -rf ~/.vhs 2>/dev/null || true
	@echo "$(GREEN)✓ VHS cache cleaned$(NC)"

# Demo management
# ============================================================================

demo-reset: media-reset ## Reset demo environment (alias)

demo-data: ## Show demo data files
	@echo "$(BLUE)Demo Data Files:$(NC)"
	@ls -lh examples/demo/ 2>/dev/null || echo "No demo files"

demo-prepare: media-reset ## Prepare demo environment
	@echo "$(BLUE)Preparing demo environment...$(NC)"
	@$(MAKE) media-reset
	@echo "$(GREEN)✓ Demo ready$(NC)"

# Media shortcuts
# ============================================================================

video: media-all ## Shortcut for media-all
screenshots: media-screenshots ## Shortcut for media-screenshots
