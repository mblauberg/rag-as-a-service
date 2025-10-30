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
