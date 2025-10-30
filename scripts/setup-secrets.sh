#!/usr/bin/env bash
# Setup script for RaaS secret configuration
# Generates both .env (Docker Compose) and secret.yaml (Kubernetes) from user input

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Validation functions
validate_openai_key() {
    local key=$1
    if [[ $key =~ ^sk-(proj-)?[A-Za-z0-9_-]{20,}$ ]]; then
        return 0
    else
        return 1
    fi
}

validate_anthropic_key() {
    local key=$1
    if [[ -z $key ]] || [[ $key =~ ^sk-ant-[A-Za-z0-9_-]{20,}$ ]]; then
        return 0
    else
        return 1
    fi
}

validate_google_key() {
    local key=$1
    # Google keys are typically 39 characters alphanumeric
    if [[ -z $key ]] || [[ $key =~ ^[A-Za-z0-9_-]{20,}$ ]]; then
        return 0
    else
        return 1
    fi
}

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}🔐 RaaS Secret Configuration Setup${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check if files already exist
ENV_FILE=".env"
K8S_SECRET_FILE="infrastructure/k8s/base/generator/secret.yaml"

if [[ -f "$ENV_FILE" ]] && [[ -f "$K8S_SECRET_FILE" ]]; then
    echo -e "${YELLOW}⚠️  Warning: Secret files already exist:${NC}"
    echo -e "  - $ENV_FILE"
    echo -e "  - $K8S_SECRET_FILE"
    echo ""
    read -p "Overwrite existing files? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}ℹ️  Setup cancelled. Existing files preserved.${NC}"
        exit 0
    fi
elif [[ -f "$ENV_FILE" ]]; then
    echo -e "${YELLOW}⚠️  Warning: $ENV_FILE already exists${NC}"
    read -p "Overwrite? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}ℹ️  Setup cancelled.${NC}"
        exit 0
    fi
elif [[ -f "$K8S_SECRET_FILE" ]]; then
    echo -e "${YELLOW}⚠️  Warning: $K8S_SECRET_FILE already exists${NC}"
    read -p "Overwrite? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}ℹ️  Setup cancelled.${NC}"
        exit 0
    fi
fi

echo ""

# Prompt for API keys
echo -e "${BLUE}Enter your API keys:${NC}"
echo -e "${BLUE}(Required keys must be filled, optional keys can be left empty)${NC}"
echo ""

# OpenAI (Required)
while true; do
    read -sp "OpenAI API Key (required): " OPENAI_KEY
    echo ""

    if [[ -z "$OPENAI_KEY" ]]; then
        echo -e "${RED}✗ OpenAI API key is required${NC}"
        continue
    fi

    if validate_openai_key "$OPENAI_KEY"; then
        echo -e "${GREEN}✓ OpenAI key format valid${NC}"
        break
    else
        echo -e "${RED}✗ Invalid OpenAI key format. Should start with 'sk-' or 'sk-proj-'${NC}"
    fi
done

echo ""

# Anthropic (Optional)
while true; do
    read -sp "Anthropic API Key (optional, press Enter to skip): " ANTHROPIC_KEY
    echo ""

    if [[ -z "$ANTHROPIC_KEY" ]]; then
        echo -e "${YELLOW}⊘ Skipping Anthropic API key${NC}"
        ENABLE_ANTHROPIC="false"
        break
    fi

    if validate_anthropic_key "$ANTHROPIC_KEY"; then
        echo -e "${GREEN}✓ Anthropic key format valid${NC}"
        ENABLE_ANTHROPIC="true"
        break
    else
        echo -e "${RED}✗ Invalid Anthropic key format. Should start with 'sk-ant-'${NC}"
    fi
done

echo ""

# Google (Optional)
while true; do
    read -sp "Google API Key (optional, press Enter to skip): " GOOGLE_KEY
    echo ""

    if [[ -z "$GOOGLE_KEY" ]]; then
        echo -e "${YELLOW}⊘ Skipping Google API key${NC}"
        ENABLE_GOOGLE="false"
        break
    fi

    if validate_google_key "$GOOGLE_KEY"; then
        echo -e "${GREEN}✓ Google key format valid${NC}"
        ENABLE_GOOGLE="true"
        break
    else
        echo -e "${RED}✗ Invalid Google key format${NC}"
    fi
done

echo ""
