# ============================================================================
# docker.mk - Docker and Docker Compose operations
# ============================================================================

.PHONY: docker-build docker-run docker-shell docker-clean docker-prune
.PHONY: compose-up compose-down compose-restart compose-logs compose-ps
.PHONY: compose-up-postgres compose-up-ai compose-up-worker
.PHONY: compose-up-full docker-test docker-health

# Docker image configuration
DOCKER_IMAGE := $(PROJECT_NAME):latest
DOCKER_TAG ?= latest
DOCKER_BUILD_ARGS ?=

# Docker build targets
# ============================================================================

docker-build: check-docker ## Build Docker image (multi-stage)
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t $(DOCKER_IMAGE) $(DOCKER_BUILD_ARGS) .
	@echo "$(GREEN)✓ Docker image built: $(DOCKER_IMAGE)$(NC)"

docker-build-no-cache: check-docker ## Build Docker image without cache
	@echo "$(BLUE)Building Docker image (no cache)...$(NC)"
	docker build --no-cache -t $(DOCKER_IMAGE) .
	@echo "$(GREEN)✓ Docker image built$(NC)"

docker-build-dev: check-docker ## Build Docker image for development
	@echo "$(BLUE)Building development Docker image...$(NC)"
	docker build \
		--target builder \
		-t $(PROJECT_NAME):dev \
		.
	@echo "$(GREEN)✓ Development image built$(NC)"

# Docker run targets
# ============================================================================

docker-run: check-docker docker-build ## Build and run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	docker run -it --rm \
		--name $(PROJECT_NAME) \
		-v $(PWD)/.env:/app/.env:ro \
		-v openfatture_data:/root/.openfatture/data \
		-v openfatture_archivio:/root/.openfatture/archivio \
		$(DOCKER_IMAGE) --help

docker-shell: check-docker docker-build ## Run Docker container with shell
	@echo "$(BLUE)Starting Docker shell...$(NC)"
	docker run -it --rm \
		--name $(PROJECT_NAME)-shell \
		-v $(PWD)/.env:/app/.env:ro \
		-v openfatture_data:/root/.openfatture/data \
		--entrypoint /bin/bash \
		$(DOCKER_IMAGE)

docker-interactive: check-docker docker-build ## Run OpenFatture in interactive mode
	@echo "$(BLUE)Starting OpenFatture interactive mode...$(NC)"
	docker run -it --rm \
		--name $(PROJECT_NAME)-interactive \
		-v $(PWD)/.env:/app/.env:ro \
		-v openfatture_data:/root/.openfatture/data \
		-v openfatture_archivio:/root/.openfatture/archivio \
		$(DOCKER_IMAGE) -i

# Docker maintenance
# ============================================================================

docker-clean: ## Remove Docker containers and images
	@echo "$(BLUE)Cleaning Docker resources...$(NC)"
	@docker rm -f $$(docker ps -aq --filter name=$(PROJECT_NAME)) 2>/dev/null || true
	@docker rmi $(DOCKER_IMAGE) 2>/dev/null || true
	@echo "$(GREEN)✓ Docker resources cleaned$(NC)"

docker-prune: ## Prune unused Docker resources
	@echo "$(BLUE)Pruning Docker resources...$(NC)"
	docker system prune -f
	@echo "$(GREEN)✓ Docker resources pruned$(NC)"

docker-volumes-clean: ## Remove Docker volumes
	@echo "$(YELLOW)⚠️  This will delete all OpenFatture data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker volume rm openfatture_data openfatture_archivio openfatture_certs openfatture_bank 2>/dev/null || true; \
		echo "$(GREEN)✓ Volumes removed$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

# Docker Compose targets
# ============================================================================

compose-up: check-docker ## Start all services (basic profile)
	@echo "$(BLUE)Starting services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo "$(YELLOW)Run '$(CYAN)make compose-logs$(YELLOW)' to view logs$(NC)"

compose-up-postgres: check-docker ## Start services with PostgreSQL
	@echo "$(BLUE)Starting services with PostgreSQL...$(NC)"
	docker-compose --profile postgres up -d
	@echo "$(GREEN)✓ Services started with PostgreSQL$(NC)"

compose-up-ai: check-docker ## Start services with AI support (Redis)
	@echo "$(BLUE)Starting services with AI support...$(NC)"
	docker-compose --profile ai up -d
	@echo "$(GREEN)✓ Services started with AI support$(NC)"

compose-up-worker: check-docker ## Start services with payment worker
	@echo "$(BLUE)Starting services with payment worker...$(NC)"
	docker-compose --profile worker up -d
	@echo "$(GREEN)✓ Services started with worker$(NC)"

compose-up-full: check-docker ## Start all services with all profiles
	@echo "$(BLUE)Starting all services (full stack)...$(NC)"
	docker-compose \
		--profile postgres \
		--profile ai \
		--profile worker \
		up -d
	@echo "$(GREEN)✓ Full stack started$(NC)"
	@echo "$(BLUE)Services:$(NC)"
	@echo "  - OpenFatture CLI"
	@echo "  - PostgreSQL (port 5432)"
	@echo "  - Redis (port 6379)"
	@echo "  - Payment Worker"

compose-down: ## Stop all services
	@echo "$(BLUE)Stopping services...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

compose-down-volumes: ## Stop services and remove volumes
	@echo "$(YELLOW)⚠️  This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "$(GREEN)✓ Services stopped and volumes removed$(NC)"; \
	else \
		echo "$(YELLOW)Cancelled$(NC)"; \
	fi

compose-restart: compose-down compose-up ## Restart all services

compose-logs: ## View logs from all services
	@echo "$(BLUE)Viewing logs (Ctrl+C to exit)...$(NC)"
	docker-compose logs -f

compose-logs-openfatture: ## View OpenFatture logs only
	@echo "$(BLUE)Viewing OpenFatture logs...$(NC)"
	docker-compose logs -f openfatture

compose-logs-worker: ## View payment worker logs
	@echo "$(BLUE)Viewing payment worker logs...$(NC)"
	docker-compose logs -f payment_worker

compose-ps: ## Show running services
	@echo "$(BLUE)Running services:$(NC)"
	@docker-compose ps

compose-exec: ## Execute command in running container (usage: make compose-exec CMD="openfatture --help")
	@echo "$(BLUE)Executing in container...$(NC)"
	docker-compose exec openfatture $(CMD)

compose-shell: ## Open shell in running container
	@echo "$(BLUE)Opening shell...$(NC)"
	docker-compose exec openfatture /bin/bash

# Docker testing
# ============================================================================

docker-test: docker-build ## Test Docker image
	@echo "$(BLUE)Testing Docker image...$(NC)"
	@echo "$(BLUE)  → Testing CLI...$(NC)"
	@docker run --rm $(DOCKER_IMAGE) --help
	@echo "$(BLUE)  → Testing payment module...$(NC)"
	@docker run --rm $(DOCKER_IMAGE) payment --help
	@echo "$(GREEN)✓ Docker image tests passed$(NC)"

docker-health: ## Check health of running containers
	@echo "$(BLUE)Checking container health...$(NC)"
	@docker ps --filter name=$(PROJECT_NAME) --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

docker-inspect: ## Inspect Docker image
	@echo "$(BLUE)Inspecting Docker image...$(NC)"
	@docker inspect $(DOCKER_IMAGE) | jq '.[0] | {Id, Size, Created, Config: {Env, Cmd, Entrypoint, WorkingDir}}'

# Docker shortcuts
# ============================================================================

db: docker-build ## Shortcut for docker-build
dr: docker-run ## Shortcut for docker-run
ds: docker-shell ## Shortcut for docker-shell
cu: compose-up ## Shortcut for compose-up
cd: compose-down ## Shortcut for compose-down
cl: compose-logs ## Shortcut for compose-logs
