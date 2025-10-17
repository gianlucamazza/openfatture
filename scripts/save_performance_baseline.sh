#!/bin/bash
# Save performance test baseline
#
# Usage:
#   ./scripts/save_performance_baseline.sh [baseline_name]
#
# Examples:
#   ./scripts/save_performance_baseline.sh main
#   ./scripts/save_performance_baseline.sh v1.2.0

set -e

BASELINE_NAME="${1:-baseline}"
BASELINE_DIR=".performance-baselines"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "📊 Running performance tests to establish baseline: $BASELINE_NAME"
echo ""

# Create baseline directory
mkdir -p "$BASELINE_DIR"

# Run performance tests and save results
echo "Running tests..."
uv run pytest -v -m performance \
  --tb=short \
  --no-cov \
  -o log_cli=false \
  --quiet

# Create baseline metadata
cat > "$BASELINE_DIR/${BASELINE_NAME}_${TIMESTAMP}.json" << EOF
{
  "name": "$BASELINE_NAME",
  "timestamp": "$TIMESTAMP",
  "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "git_branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
  "python_version": "$(python --version 2>&1)",
  "system": "$(uname -s)",
  "arch": "$(uname -m)"
}
EOF

# Create symlink to latest baseline
ln -sf "${BASELINE_NAME}_${TIMESTAMP}.json" "$BASELINE_DIR/latest.json"

echo ""
echo "✅ Baseline saved:"
echo "   - File: $BASELINE_DIR/${BASELINE_NAME}_${TIMESTAMP}.json"
echo "   - Git commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
echo "   - Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
echo ""
echo "📝 To compare with this baseline in the future:"
echo "   export PERFORMANCE_BASELINE=$BASELINE_NAME"
echo "   make test-performance"
