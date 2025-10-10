#!/usr/bin/env bash

# Check Ollama availability and model readiness for media automation
# Usage:
#   ./scripts/check_ollama.sh                    # Check default model (llama3.2)
#   ./scripts/check_ollama.sh mistral-small3.1   # Check specific model

set -euo pipefail

MODEL="${1:-llama3.2}"
OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
TIMEOUT=5

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ${NC}  $*"
}

log_success() {
    echo -e "${GREEN}✓${NC}  $*"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC}  $*"
}

log_error() {
    echo -e "${RED}✗${NC}  $*" >&2
}

# Check if Ollama is installed
check_ollama_installed() {
    if ! command -v ollama >/dev/null 2>&1; then
        log_error "Ollama is not installed"
        echo ""
        echo "Install Ollama from: https://ollama.com/download"
        echo "  macOS:   brew install ollama"
        echo "  Linux:   curl -fsSL https://ollama.com/install.sh | sh"
        return 1
    fi

    log_success "Ollama binary found: $(which ollama)"
    return 0
}

# Check if Ollama service is running
check_ollama_service() {
    log_info "Checking Ollama service at ${OLLAMA_BASE_URL}..."

    if curl -s --max-time "${TIMEOUT}" "${OLLAMA_BASE_URL}/api/tags" >/dev/null 2>&1; then
        log_success "Ollama service is running"
        return 0
    else
        log_error "Ollama service is not responding at ${OLLAMA_BASE_URL}"
        echo ""
        echo "Start Ollama with:"
        echo "  ollama serve"
        echo ""
        echo "Or if using the macOS app, ensure it's running."
        return 1
    fi
}

# Check if model is available
check_model_available() {
    log_info "Checking if model '${MODEL}' is available..."

    # List available models
    AVAILABLE_MODELS=$(curl -s --max-time "${TIMEOUT}" "${OLLAMA_BASE_URL}/api/tags" | \
        grep -o '"name":"[^"]*"' | \
        sed 's/"name":"//g' | \
        sed 's/"//g' || echo "")

    if echo "${AVAILABLE_MODELS}" | grep -q "^${MODEL}"; then
        log_success "Model '${MODEL}' is available"
        return 0
    else
        log_warning "Model '${MODEL}' is not available locally"
        echo ""
        echo "Available models:"
        echo "${AVAILABLE_MODELS}" | sed 's/^/  - /'
        echo ""
        echo "Pull the model with:"
        echo "  ollama pull ${MODEL}"
        return 1
    fi
}

# Auto-pull model if requested
auto_pull_model() {
    log_info "Pulling model '${MODEL}'..."

    if ollama pull "${MODEL}"; then
        log_success "Model '${MODEL}' pulled successfully"
        return 0
    else
        log_error "Failed to pull model '${MODEL}'"
        return 1
    fi
}

# Test model inference
test_model_inference() {
    log_info "Testing model inference..."

    local test_prompt="Say 'OK' in one word"
    local response

    response=$(curl -s --max-time 30 "${OLLAMA_BASE_URL}/api/generate" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"${MODEL}\",
            \"prompt\": \"${test_prompt}\",
            \"stream\": false
        }" | grep -o '"response":"[^"]*"' | sed 's/"response":"//;s/"$//' || echo "")

    if [ -n "${response}" ]; then
        log_success "Model inference working (response: ${response})"
        return 0
    else
        log_error "Model inference failed or timed out"
        return 1
    fi
}

# Main execution
main() {
    echo ""
    echo "🤖 Ollama Health Check for Media Automation"
    echo "==========================================="
    echo ""

    local exit_code=0

    # Step 1: Check installation
    if ! check_ollama_installed; then
        exit 1
    fi

    # Step 2: Check service
    if ! check_ollama_service; then
        exit 1
    fi

    # Step 3: Check model availability
    if ! check_model_available; then
        echo ""
        read -p "Pull model '${MODEL}' now? [y/N] " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if ! auto_pull_model; then
                exit 1
            fi
        else
            log_warning "Skipping model pull. Media automation may fail without this model."
            exit_code=1
        fi
    fi

    # Step 4: Test inference (optional - can be slow)
    if [ "${SKIP_INFERENCE_TEST:-0}" != "1" ]; then
        if ! test_model_inference; then
            log_warning "Inference test failed. Model may not be fully functional."
            exit_code=1
        fi
    fi

    echo ""
    if [ $exit_code -eq 0 ]; then
        echo "🎉 All checks passed! Ollama is ready for media automation."
    else
        echo "⚠️  Some checks failed. Please review warnings above."
    fi
    echo ""

    return $exit_code
}

# Run main if executed directly
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
