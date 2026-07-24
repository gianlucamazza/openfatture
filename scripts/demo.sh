#!/usr/bin/env bash
set -euo pipefail

echo "OpenFatture CLI demo"
echo
uv run openfatture --version
uv run openfatture --help
uv run openfatture status --json
uv run openfatture assistant --help
uv run openfatture interactive --help
echo
echo "Demo completed without external provider calls."
