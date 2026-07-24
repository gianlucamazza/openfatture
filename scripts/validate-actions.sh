#!/usr/bin/env bash

set -euo pipefail

if ! command -v actionlint >/dev/null 2>&1; then
  echo "actionlint is required to validate GitHub Actions workflows" >&2
  exit 1
fi

if ! command -v act >/dev/null 2>&1; then
  echo "act is required to inspect workflow plans" >&2
  exit 1
fi

echo "Validating GitHub Actions syntax"
actionlint .github/workflows/*.yml

echo "Listing workflow jobs"
act -l

echo "Dry-running the deterministic demo workflow"
act -n workflow_dispatch \
  -W .github/workflows/demo-validation.yml \
  --container-architecture linux/amd64

echo "GitHub Actions validation completed"
