#!/usr/bin/env bash

# Reset the OpenFatture demo environment with deterministic seed data.
# Usage:
#   ./scripts/reset_demo.sh            # uses openfatture_demo.db
#   ./scripts/reset_demo.sh custom.db  # custom SQLite filename

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

DB_FILE="${1:-openfatture_demo.db}"
DB_URL="sqlite:///./${DB_FILE}"

export DATABASE_URL="${DB_URL}"
export CEDENTE_DENOMINAZIONE="OpenFatture Demo Studio"
export CEDENTE_PARTITA_IVA="04567890123"
export CEDENTE_CODICE_FISCALE="DMOGLC85A01H501Y"
export CEDENTE_REGIME_FISCALE="RF19"
export CEDENTE_INDIRIZZO="Via Digitale 42"
export CEDENTE_CAP="20100"
export CEDENTE_COMUNE="Milano"
export CEDENTE_PROVINCIA="MI"
export CEDENTE_NAZIONE="IT"
export CEDENTE_TELEFONO="+39 02 1234567"
export CEDENTE_EMAIL="demo@openfatture.dev"

export PEC_ADDRESS="openfatture-demo@pec.it"
export PEC_PASSWORD="demo-password"
export PEC_SMTP_SERVER="smtp.pec.aruba.it"
export PEC_SMTP_PORT="465"
export SDI_PEC_ADDRESS="sdi01@pec.fatturapa.it"

export NOTIFICATION_EMAIL="team@openfatture.dev"
export NOTIFICATION_ENABLED="true"

# AI Configuration - Ollama for deterministic demo (no API keys needed)
export AI_PROVIDER="${AI_PROVIDER:-ollama}"
export AI_MODEL="${AI_MODEL:-llama3.2}"
export OPENFATTURE_AI_OLLAMA_BASE_URL="${OPENFATTURE_AI_OLLAMA_BASE_URL:-http://localhost:11434}"
export AI_TEMPERATURE="${AI_TEMPERATURE:-0.7}"
export AI_MAX_TOKENS="${AI_MAX_TOKENS:-2000}"
export AI_CHAT_ENABLED="${AI_CHAT_ENABLED:-true}"
export AI_TOOLS_ENABLED="${AI_TOOLS_ENABLED:-false}"

if ! command -v uv >/dev/null 2>&1; then
  echo "❌ uv is required. Install from https://astral.sh/uv/ and retry." >&2
  exit 1
fi

# Check Ollama if using ollama provider
if [ "${AI_PROVIDER}" = "ollama" ]; then
  echo "🤖 Checking Ollama availability..."
  if [ -f "${SCRIPT_DIR}/check_ollama.sh" ]; then
    SKIP_INFERENCE_TEST=1 "${SCRIPT_DIR}/check_ollama.sh" "${AI_MODEL}" || {
      echo "⚠️  Ollama check failed. Demo will continue but AI features may not work." >&2
    }
  else
    echo "⚠️  check_ollama.sh not found. Skipping Ollama health check." >&2
  fi
  echo ""
fi

echo "🔄 Resetting demo dataset at ${DB_URL}"

(
  cd "${PROJECT_ROOT}"
  uv run python scripts/reset_demo.py
)

echo "✅ Demo environment ready."
echo "   Database file: ${PROJECT_ROOT}/${DB_FILE}"
