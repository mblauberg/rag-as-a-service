#!/bin/bash

################################################################################
# RAAS Integration Test Script
#
# This script tests the full workflow of the RAAS platform:
# 1. Starts all services via Docker Compose
# 2. Waits for services to be healthy
# 3. Tests document upload, search, retrieval, and deletion
# 4. Verifies frontend accessibility
# 5. Provides cleanup options
################################################################################

set -e  # Exit on error
set -o pipefail  # Exit on pipe failure

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MAX_WAIT_TIME=180  # Maximum time to wait for services (seconds)
API_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"
EMBEDDER_URL="http://localhost:8001"
TEST_DOC_PATH="/tmp/raas_test_doc.txt"
DOCKER_COMPOSE_FILE="infrastructure/docker-compose/docker-compose.yml"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TEST_RESULTS=()

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

record_test() {
    local test_name="$1"
    local result="$2"

    if [ "$result" == "PASS" ]; then
        ((TESTS_PASSED++))
        TEST_RESULTS+=("${GREEN}✓${NC} $test_name")
        print_success "$test_name"
    else
        ((TESTS_FAILED++))
        TEST_RESULTS+=("${RED}✗${NC} $test_name")
        print_error "$test_name"
    fi
}

wait_for_service() {
    local service_name="$1"
    local url="$2"
    local max_attempts=$((MAX_WAIT_TIME / 5))
    local attempt=0

    print_info "Waiting for $service_name to be ready..."

    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            print_success "$service_name is ready"
            return 0
        fi

        ((attempt++))
        echo -n "."
        sleep 5
    done

    print_error "$service_name failed to become ready after ${MAX_WAIT_TIME}s"
    return 1
}

################################################################################
# Pre-flight Checks
################################################################################

preflight_checks() {
    print_header "Pre-flight Checks"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_success "Docker is installed"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    print_success "Docker Compose is installed"

    # Check if we're in the right directory
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        print_error "Docker Compose file not found at $DOCKER_COMPOSE_FILE"
        print_info "Please run this script from the repository root"
        exit 1
    fi
    print_success "Docker Compose file found"

    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    print_success "Docker daemon is running"

    echo ""
}

################################################################################
# Service Management
################################################################################

cleanup_existing_containers() {
    print_header "Cleanup"

    print_info "Stopping existing containers..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down -v > /dev/null 2>&1 || true
    print_success "Cleanup complete"
    echo ""
}

start_services() {
    print_header "Starting Services"

    print_info "Building and starting all services..."
    if docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --build; then
        print_success "Services started"
    else
        print_error "Failed to start services"
        exit 1
    fi

    echo ""

    # Wait for services to be healthy
    print_header "Waiting for Services"

    wait_for_service "API Health Check" "$API_URL/api/v1/health" || exit 1
    wait_for_service "API Ready Check" "$API_URL/api/v1/ready" || exit 1
    wait_for_service "Embedder Health Check" "$EMBEDDER_URL/api/v1/health" || exit 1
    wait_for_service "Frontend" "$FRONTEND_URL" || exit 1

    echo ""

    # Show service status
    print_header "Service Status"
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    echo ""
}

################################################################################
# Test Functions
################################################################################

test_health_endpoints() {
    print_header "Testing Health Endpoints"

    # Test API health
    if curl -s -f "$API_URL/api/v1/health" > /dev/null 2>&1; then
        record_test "API health endpoint" "PASS"
    else
        record_test "API health endpoint" "FAIL"
    fi

    # Test API ready
    if curl -s -f "$API_URL/api/v1/ready" > /dev/null 2>&1; then
        record_test "API ready endpoint" "PASS"
    else
        record_test "API ready endpoint" "FAIL"
    fi

    # Test Embedder health
    if curl -s -f "$EMBEDDER_URL/api/v1/health" > /dev/null 2>&1; then
        record_test "Embedder health endpoint" "PASS"
    else
        record_test "Embedder health endpoint" "FAIL"
    fi

    # Test Frontend
    if curl -s -f "$FRONTEND_URL" > /dev/null 2>&1; then
        record_test "Frontend accessibility" "PASS"
    else
        record_test "Frontend accessibility" "FAIL"
    fi

    echo ""
}

test_document_upload() {
    print_header "Testing Document Upload"

    # Create test document
    echo "This is a test document for RAAS integration testing. It contains sample text about artificial intelligence, machine learning, and natural language processing." > "$TEST_DOC_PATH"

    # Upload document
    local response=$(curl -s -X POST "$API_URL/api/v1/documents/upload" \
        -F "file=@$TEST_DOC_PATH" \
        -F "title=Integration Test Document" \
        -F "description=Test document for integration testing")

    # Check if upload was successful
    if echo "$response" | grep -q '"id"'; then
        DOCUMENT_ID=$(echo "$response" | grep -o '"id": *"[^"]*"' | head -1 | grep -o '"[0-9a-f-]*"' | tr -d '"')
        record_test "Document upload" "PASS"
        print_info "Document ID: $DOCUMENT_ID"
    else
        record_test "Document upload" "FAIL"
        print_info "Response: $response"
        DOCUMENT_ID=""
    fi

    echo ""
}

test_document_retrieval() {
    print_header "Testing Document Retrieval"

    if [ -z "$DOCUMENT_ID" ]; then
        record_test "Document retrieval (skipped - no document ID)" "FAIL"
        echo ""
        return
    fi

    # Wait a moment for processing
    print_info "Waiting for document processing..."
    sleep 5

    # Retrieve document
    local response=$(curl -s -f "$API_URL/api/v1/documents/$DOCUMENT_ID")

    if echo "$response" | grep -q '"id"'; then
        record_test "Document retrieval" "PASS"

        # Check embedding status
        if echo "$response" | grep -q '"embedding_status":"completed"'; then
            record_test "Document embedding completed" "PASS"
        else
            record_test "Document embedding completed" "FAIL"
            print_info "Embedding status: $(echo "$response" | grep -o '"embedding_status":"[^"]*"')"
        fi
    else
        record_test "Document retrieval" "FAIL"
    fi

    echo ""
}

test_search_functionality() {
    print_header "Testing Search Functionality"

    if [ -z "$DOCUMENT_ID" ]; then
        record_test "Search functionality (skipped - no document)" "FAIL"
        echo ""
        return
    fi

    # Wait for embeddings to be processed
    print_info "Waiting for embeddings to be processed..."
    sleep 10

    # Perform search
    local response=$(curl -s -X POST "$API_URL/api/v1/search" \
        -H "Content-Type: application/json" \
        -d '{"query":"artificial intelligence machine learning","limit":5}')

    if echo "$response" | grep -q '"chunks"'; then
        record_test "Search query execution" "PASS"

        # Check if results contain our document
        if echo "$response" | grep -q "Integration Test Document"; then
            record_test "Search results contain uploaded document" "PASS"
        else
            record_test "Search results contain uploaded document" "FAIL"
            print_info "Response: $response"
        fi
    else
        record_test "Search query execution" "FAIL"
        print_info "Response: $response"
    fi

    echo ""
}

test_document_deletion() {
    print_header "Testing Document Deletion"

    if [ -z "$DOCUMENT_ID" ]; then
        record_test "Document deletion (skipped - no document ID)" "FAIL"
        echo ""
        return
    fi

    # Delete document
    local status_code=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "$API_URL/api/v1/documents/$DOCUMENT_ID")

    if [ "$status_code" == "204" ] || [ "$status_code" == "200" ]; then
        record_test "Document deletion" "PASS"

        # Verify document is deleted
        local verify_code=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/v1/documents/$DOCUMENT_ID")
        if [ "$verify_code" == "404" ]; then
            record_test "Document deletion verification" "PASS"
        else
            record_test "Document deletion verification" "FAIL"
        fi
    else
        record_test "Document deletion" "FAIL"
        print_info "Status code: $status_code"
    fi

    echo ""
}

test_list_documents() {
    print_header "Testing Document Listing"

    local response=$(curl -s -f "$API_URL/api/v1/documents")

    if echo "$response" | grep -q '\['; then
        record_test "List documents endpoint" "PASS"
    else
        record_test "List documents endpoint" "FAIL"
        print_info "Response: $response"
    fi

    echo ""
}

################################################################################
# Results and Cleanup
################################################################################

show_results() {
    print_header "Test Results"

    for result in "${TEST_RESULTS[@]}"; do
        echo -e "$result"
    done

    echo ""
    echo -e "${BLUE}Total Tests: $((TESTS_PASSED + TESTS_FAILED))${NC}"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    echo ""

    if [ $TESTS_FAILED -eq 0 ]; then
        print_success "All tests passed!"
        return 0
    else
        print_error "Some tests failed"
        return 1
    fi
}

cleanup_prompt() {
    print_header "Cleanup"

    echo -e "${YELLOW}Do you want to keep the services running? (y/n)${NC}"
    read -r response

    if [[ "$response" =~ ^([nN][oO]|[nN])$ ]]; then
        print_info "Stopping services..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" down -v
        print_success "Services stopped and volumes removed"
    else
        print_info "Services are still running"
        print_info "To stop them later, run: docker-compose -f $DOCKER_COMPOSE_FILE down -v"
        echo ""
        print_info "Access the services at:"
        echo "  - Frontend: $FRONTEND_URL"
        echo "  - API: $API_URL/api/v1/docs"
        echo "  - Embedder: $EMBEDDER_URL/docs"
    fi

    # Cleanup test file
    rm -f "$TEST_DOC_PATH"

    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    clear
    print_header "RAAS Integration Test Suite"
    echo ""

    # Run preflight checks
    preflight_checks

    # Cleanup existing containers
    cleanup_existing_containers

    # Start services
    start_services

    # Run tests
    test_health_endpoints
    test_list_documents
    test_document_upload
    test_document_retrieval
    test_search_functionality
    test_document_deletion

    # Show results
    show_results
    TEST_EXIT_CODE=$?

    # Cleanup prompt
    cleanup_prompt

    # Exit with appropriate code
    exit $TEST_EXIT_CODE
}

# Run main function
main
