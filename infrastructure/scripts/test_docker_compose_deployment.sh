#!/bin/bash

# Test script for docker-compose deployment workflow
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Testing Docker Compose Deployment Workflow ===${NC}\n"

# Store the project root
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="infrastructure/docker-compose/docker-compose.yml"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Checking .env.template...${NC}"
    if [ -f ".env.template" ]; then
        echo -e "${YELLOW}Creating .env from .env.template...${NC}"
        cp .env.template .env
        echo -e "${YELLOW}Please update .env with your API keys before running this test again.${NC}"
        exit 1
    else
        echo -e "${RED}Error: Neither .env nor .env.template found${NC}"
        exit 1
    fi
fi

# Function to cleanup
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    docker-compose -f "$COMPOSE_FILE" down -v 2>/dev/null || true
    echo -e "${GREEN}Cleanup complete${NC}"
}

# Set trap to cleanup on exit
trap cleanup EXIT

echo -e "${GREEN}Step 1: Validating docker-compose configuration${NC}"
if docker-compose -f "$COMPOSE_FILE" config > /dev/null; then
    echo -e "${GREEN}✓ Docker Compose configuration is valid${NC}\n"
else
    echo -e "${RED}✗ Docker Compose configuration is invalid${NC}"
    exit 1
fi

echo -e "${GREEN}Step 2: Starting services${NC}"
if docker-compose -f "$COMPOSE_FILE" up -d; then
    echo -e "${GREEN}✓ Services started successfully${NC}\n"
else
    echo -e "${RED}✗ Failed to start services${NC}"
    exit 1
fi

echo -e "${GREEN}Step 3: Waiting for services to be healthy (up to 60 seconds)${NC}"
TIMEOUT=60
ELAPSED=0
ALL_HEALTHY=false

while [ $ELAPSED -lt $TIMEOUT ]; do
    # Check if all services are running
    RUNNING=$(docker-compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | wc -l)
    TOTAL=$(docker-compose -f "$COMPOSE_FILE" ps --services | wc -l)

    echo -e "  Running: $RUNNING/$TOTAL services"

    if [ "$RUNNING" -eq "$TOTAL" ]; then
        ALL_HEALTHY=true
        break
    fi

    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

if [ "$ALL_HEALTHY" = true ]; then
    echo -e "${GREEN}✓ All services are healthy${NC}\n"
else
    echo -e "${RED}✗ Not all services became healthy within timeout${NC}"
    echo -e "${YELLOW}Service status:${NC}"
    docker-compose -f "$COMPOSE_FILE" ps
    exit 1
fi

echo -e "${YELLOW}Waiting for services to fully initialize...${NC}"

# Function to check endpoint with retry
check_endpoint() {
    local url=$1
    local name=$2
    local max_attempts=12
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -f "$url" > /dev/null 2>&1; then
            return 0
        fi
        echo "  Attempt $attempt/$max_attempts for $name..."
        sleep 5
        attempt=$((attempt + 1))
    done
    return 1
}

echo -e "\n${GREEN}Step 4: Checking service endpoints${NC}"

# Check API health
echo "  Checking API service..."
if check_endpoint "http://localhost:8000/api/v1/health" "API"; then
    echo -e "${GREEN}✓ API service is responding${NC}"
else
    echo -e "${RED}✗ API service is not responding after 60 seconds${NC}"
    docker-compose -f "$COMPOSE_FILE" logs api | tail -20
    exit 1
fi

# Check Frontend
echo "  Checking Frontend service..."
if check_endpoint "http://localhost:3000" "Frontend"; then
    echo -e "${GREEN}✓ Frontend service is responding${NC}"
else
    echo -e "${RED}✗ Frontend service is not responding after 60 seconds${NC}"
    docker-compose -f "$COMPOSE_FILE" logs frontend | tail -20
    exit 1
fi

# Check Qdrant
echo "  Checking Qdrant service..."
if check_endpoint "http://localhost:6333" "Qdrant"; then
    echo -e "${GREEN}✓ Qdrant service is responding${NC}"
else
    echo -e "${RED}✗ Qdrant service is not responding after 60 seconds${NC}"
    docker-compose -f "$COMPOSE_FILE" logs qdrant | tail -20
    exit 1
fi

# Check Embedder
echo "  Checking Embedder service..."
if check_endpoint "http://localhost:8001/api/v1/health" "Embedder"; then
    echo -e "${GREEN}✓ Embedder service is responding${NC}"
else
    echo -e "${RED}✗ Embedder service is not responding after 60 seconds${NC}"
    docker-compose -f "$COMPOSE_FILE" logs embedder | tail -20
    exit 1
fi

# Check Generator
echo "  Checking Generator service..."
if check_endpoint "http://localhost:8002/api/v1/health" "Generator"; then
    echo -e "${GREEN}✓ Generator service is responding${NC}"
else
    echo -e "${RED}✗ Generator service is not responding after 60 seconds${NC}"
    docker-compose -f "$COMPOSE_FILE" logs generator | tail -20
    exit 1
fi

echo -e "\n${GREEN}Step 5: Verifying service logs${NC}"
docker-compose -f "$COMPOSE_FILE" logs --tail=10

echo -e "\n${GREEN}=== Docker Compose Deployment Test PASSED ===${NC}"
echo -e "${GREEN}All services are running and responding correctly!${NC}\n"

echo -e "${YELLOW}Services accessible at:${NC}"
echo "  - Frontend: http://localhost:3000"
echo "  - API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Qdrant: http://localhost:6333"
echo "  - Embedder: http://localhost:8001"
echo -e "  - Generator: http://localhost:8002\n"

exit 0
