#!/usr/bin/env bash

set -euo pipefail

if ! command -v act >/dev/null 2>&1; then
  echo "act is required; install it from https://github.com/nektos/act" >&2
  exit 1
fi

JOB="${1:-demo}"
WORKFLOW="${2:-.github/workflows/demo-validation.yml}"

if [[ "$JOB" == "list" ]]; then
  exec act -l
fi

if [[ "$JOB" == "dry-run" ]]; then
  exec act -n workflow_dispatch -W "$WORKFLOW" --container-architecture linux/amd64
fi

echo "Running workflow job: $JOB"
echo "Workflow: $WORKFLOW"
exec act workflow_dispatch \
  -j "$JOB" \
  -W "$WORKFLOW" \
  --container-architecture linux/amd64
