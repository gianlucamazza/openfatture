#!/bin/bash
#
# Setup act secrets using GitHub CLI or fallback to manual configuration
# This script automatically configures GITHUB_TOKEN from gh if available
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SECRETS_FILE=".secrets"
SECRETS_EXAMPLE=".secrets.example"

# Check if gh is installed and authenticated
if command -v gh &> /dev/null; then
    if gh auth status &> /dev/null; then
        echo -e "${GREEN}✓ GitHub CLI is authenticated${NC}"

        # Get token from gh
        GH_TOKEN=$(gh auth token)

        # Create or update .secrets file
        if [ -f "$SECRETS_FILE" ]; then
            # Update existing file, preserving other secrets
            if grep -q "^GITHUB_TOKEN=" "$SECRETS_FILE"; then
                # Replace existing GITHUB_TOKEN
                sed -i.bak "s|^GITHUB_TOKEN=.*|GITHUB_TOKEN=$GH_TOKEN|" "$SECRETS_FILE" && rm "${SECRETS_FILE}.bak"
                echo -e "${GREEN}✓ Updated GITHUB_TOKEN in $SECRETS_FILE${NC}"
            else
                # Add GITHUB_TOKEN to existing file
                echo "GITHUB_TOKEN=$GH_TOKEN" >> "$SECRETS_FILE"
                echo -e "${GREEN}✓ Added GITHUB_TOKEN to $SECRETS_FILE${NC}"
            fi
        else
            # Create new .secrets from template with real token
            if [ -f "$SECRETS_EXAMPLE" ]; then
                cp "$SECRETS_EXAMPLE" "$SECRETS_FILE"
                sed -i.bak "s|^GITHUB_TOKEN=.*|GITHUB_TOKEN=$GH_TOKEN|" "$SECRETS_FILE" && rm "${SECRETS_FILE}.bak"
                echo -e "${GREEN}✓ Created $SECRETS_FILE with GitHub CLI token${NC}"
            else
                # Create minimal .secrets with just GitHub token
                cat > "$SECRETS_FILE" <<EOF
# GitHub Actions Secrets for act
# Auto-generated using GitHub CLI
GITHUB_TOKEN=$GH_TOKEN
PYPI_TOKEN=pypi-FAKE_TOKEN_FOR_LOCAL_TESTING
CODECOV_TOKEN=FAKE_CODECOV_TOKEN
EOF
                echo -e "${GREEN}✓ Created $SECRETS_FILE with GitHub CLI token${NC}"
            fi
        fi

        echo -e "${BLUE}ℹ  Using token from GitHub CLI (scope: repo)${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠️  GitHub CLI is installed but not authenticated${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  GitHub CLI (gh) is not installed${NC}"
fi

# Fallback: manual configuration
echo -e "${BLUE}Falling back to manual configuration...${NC}"

if [ ! -f "$SECRETS_FILE" ]; then
    if [ -f "$SECRETS_EXAMPLE" ]; then
        cp "$SECRETS_EXAMPLE" "$SECRETS_FILE"
        echo -e "${GREEN}✓ Created $SECRETS_FILE from template${NC}"
        echo -e "${YELLOW}⚠️  Please edit $SECRETS_FILE with your credentials${NC}"
        echo ""
        echo -e "${BLUE}To use GitHub CLI instead:${NC}"
        echo "  1. Install: brew install gh"
        echo "  2. Authenticate: gh auth login"
        echo "  3. Re-run this script"
    else
        echo -e "${RED}❌ Error: $SECRETS_EXAMPLE not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ $SECRETS_FILE already exists${NC}"
    if ! grep -q "^GITHUB_TOKEN=ghp_" "$SECRETS_FILE" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  GITHUB_TOKEN may not be configured correctly${NC}"
        echo -e "${BLUE}To auto-configure with GitHub CLI:${NC}"
        echo "  1. Install: brew install gh"
        echo "  2. Authenticate: gh auth login"
        echo "  3. Re-run this script"
    fi
fi
