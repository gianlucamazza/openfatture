#!/bin/bash
#
# Test GitHub Actions workflows locally with act
# This script runs specific jobs or complete workflows for testing
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Testing GitHub Actions locally with act...${NC}\n"

# Check if act is installed
if ! command -v act &> /dev/null; then
    echo -e "${RED}❌ Error: act is not installed${NC}"
    echo "Install with: brew install act (macOS) or visit https://github.com/nektos/act"
    exit 1
fi

# Setup secrets using GitHub CLI or fallback to manual configuration
echo -e "${BLUE}Setting up secrets...${NC}"
if [ -f scripts/setup-act-secrets.sh ]; then
    ./scripts/setup-act-secrets.sh
    echo ""
else
    echo -e "${YELLOW}⚠️  Warning: setup-act-secrets.sh not found${NC}"
    # Fallback to old behavior
    if [ ! -f .secrets ]; then
        echo -e "${YELLOW}⚠️  Warning: .secrets file not found${NC}"
        echo "Copying from .secrets.example..."
        if [ -f .secrets.example ]; then
            cp .secrets.example .secrets
            echo -e "${GREEN}✓ Created .secrets from template${NC}\n"
        else
            echo -e "${RED}❌ Error: .secrets.example not found${NC}"
            exit 1
        fi
    fi
fi

# Parse command line arguments
JOB="${1:-lint}"
WORKFLOW="${2:-.github/workflows/test.yml}"

echo -e "${BLUE}Configuration:${NC}"
echo "  Job: $JOB"
echo "  Workflow: $WORKFLOW"
echo ""

# Test specific job based on argument
case "$JOB" in
    lint)
        echo -e "${BLUE}Running lint job (fast test)...${NC}"
        act push -j lint -W .github/workflows/test.yml
        ;;

    test)
        echo -e "${BLUE}Running test job on Python 3.12...${NC}"
        act push -j test -W .github/workflows/test.yml \
            --matrix python-version:3.12 \
            --matrix os:ubuntu-latest
        ;;

    security)
        echo -e "${BLUE}Running security scan job...${NC}"
        act push -j security -W .github/workflows/test.yml
        ;;

    coverage)
        echo -e "${BLUE}Running coverage gate job...${NC}"
        act push -j coverage-gate -W .github/workflows/test.yml
        ;;

    all)
        echo -e "${BLUE}Running all test workflow jobs...${NC}"
        echo -e "${YELLOW}⚠️  This may take several minutes${NC}\n"
        act push -W .github/workflows/test.yml
        ;;

    release)
        echo -e "${BLUE}Running release workflow...${NC}"
        if [ ! -f test-event.json ]; then
            echo -e "${RED}❌ Error: test-event.json not found${NC}"
            exit 1
        fi
        act push -W .github/workflows/release.yml --eventpath test-event.json
        ;;

    list)
        echo -e "${BLUE}Available jobs in all workflows:${NC}"
        act -l
        ;;

    *)
        echo -e "${YELLOW}Testing custom job: $JOB${NC}"
        act push -j "$JOB" -W "$WORKFLOW"
        ;;
esac

echo ""
echo -e "${GREEN}✅ Test completed!${NC}"
echo -e "${BLUE}Usage examples:${NC}"
echo "  ./scripts/test-actions.sh lint              # Fast lint check"
echo "  ./scripts/test-actions.sh test              # Run tests on Python 3.12"
echo "  ./scripts/test-actions.sh security          # Security scan"
echo "  ./scripts/test-actions.sh all               # All test jobs (slow)"
echo "  ./scripts/test-actions.sh release           # Release workflow"
echo "  ./scripts/test-actions.sh list              # List all jobs"
echo ""
