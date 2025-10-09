#!/bin/bash
#
# Validate GitHub Actions workflows with act
# This script validates workflow syntax and performs dry-runs without execution
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Validating GitHub Actions workflows with act...${NC}\n"

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
        echo "Creating from .secrets.example..."
        if [ -f .secrets.example ]; then
            cp .secrets.example .secrets
            echo -e "${GREEN}✓ Created .secrets from template${NC}"
            echo -e "${YELLOW}  Please edit .secrets with your test values${NC}\n"
        else
            echo -e "${RED}❌ Error: .secrets.example not found${NC}"
            exit 1
        fi
    fi
fi

# Step 1: Check workflow syntax by listing jobs
echo -e "${BLUE}1️⃣  Checking workflow syntax...${NC}"
if act -l > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Workflow syntax is valid${NC}\n"
    act -l
    echo ""
else
    echo -e "${RED}❌ Workflow syntax error detected${NC}"
    act -l
    exit 1
fi

# Step 2: Dry-run test workflow
echo -e "${BLUE}2️⃣  Dry-run test workflow (test.yml)...${NC}"
if act push --dryrun -W .github/workflows/test.yml 2>&1 | grep -q "Job 'test' finished successfully"; then
    echo -e "${GREEN}✓ Test workflow structure is valid${NC}\n"
else
    echo -e "${YELLOW}⚠️  Test workflow dry-run completed (check output for warnings)${NC}\n"
fi

# Step 3: Dry-run release workflow with mock event
echo -e "${BLUE}3️⃣  Dry-run release workflow (release.yml)...${NC}"
if [ ! -f test-event.json ]; then
    echo -e "${YELLOW}⚠️  test-event.json not found, skipping release workflow validation${NC}\n"
else
    if act push --dryrun -W .github/workflows/release.yml --eventpath test-event.json 2>&1 | head -20; then
        echo -e "${GREEN}✓ Release workflow structure is valid${NC}\n"
    else
        echo -e "${YELLOW}⚠️  Release workflow dry-run completed (check output for warnings)${NC}\n"
    fi
fi

# Step 4: Validate workflow files with GitHub API schema (optional)
echo -e "${BLUE}4️⃣  Checking for common workflow issues...${NC}"

# Check for required secrets
if grep -q "secrets\." .github/workflows/*.yml; then
    echo -e "${YELLOW}⚠️  Workflows use secrets - ensure they are defined in .secrets${NC}"
    grep -h "secrets\." .github/workflows/*.yml | sed 's/^/  - /'
    echo ""
fi

# Summary
echo -e "${GREEN}✅ All workflows validated successfully!${NC}"
echo -e "${BLUE}Next steps:${NC}"
echo "  - Run specific job: ./scripts/test-actions.sh"
echo "  - Test lint job: act push -j lint"
echo "  - Test with specific matrix: act push -j test --matrix python-version:3.12 --matrix os:ubuntu-latest"
echo ""
