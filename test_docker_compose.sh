#!/bin/bash
set -e

echo "=== Comprehensive Docker-Compose Testing ==="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=$3
    local method=${4:-GET}

    echo -n "Testing $name... "
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url")
    fi

    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo "  Response: $body"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected HTTP $expected_code, got $http_code)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "  Response: $body"
        return 1
    fi
}

echo "1. Testing Core Service Health"
echo "================================"
test_endpoint "API Root" "http://localhost:8000/" "200"
test_endpoint "Embedder Health" "http://localhost:8001/api/v1/health" "200"
test_endpoint "Generator Health" "http://localhost:8002/api/v1/health" "200"
echo ""

echo "2. Testing API Endpoints"
echo "================================"
test_endpoint "API Docs" "http://localhost:8000/docs" "200"
test_endpoint "API OpenAPI" "http://localhost:8000/openapi.json" "200"
test_endpoint "API Health" "http://localhost:8000/api/v1/health" "200"
test_endpoint "Documents List (empty)" "http://localhost:8000/api/v1/documents" "200"
echo ""

echo "3. Testing Document Upload"
echo "================================"
# Create a test document
TEST_FILE="/tmp/test_document.txt"
echo "This is a test document for RAAS testing.
It contains multiple paragraphs to test the chunking and embedding functionality.

The document discusses various topics to ensure comprehensive testing of the system.
This includes text processing, embedding generation, and storage in Qdrant." > "$TEST_FILE"

echo -n "Uploading test document... "
upload_response=$(curl -s -w "\n%{http_code}" -X POST \
    -F "file=@$TEST_FILE" \
    -F "title=Test Document" \
    "http://localhost:8000/api/v1/documents/upload")

upload_code=$(echo "$upload_response" | tail -n 1)
upload_body=$(echo "$upload_response" | sed '$d')

if [ "$upload_code" = "201" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $upload_code)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo "  Response: $upload_body"
    DOCUMENT_ID=$(echo "$upload_body" | python3 -c "import sys, json; print(json.load(sys.stdin)['document']['id'])" 2>/dev/null || echo "")
else
    echo -e "${RED}✗ FAIL${NC} (Expected HTTP 200, got $upload_code)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo "  Response: $upload_body"
fi
echo ""

echo "4. Testing Search"
echo "================================"
if [ -n "$DOCUMENT_ID" ]; then
    echo "Document ID: $DOCUMENT_ID"

    # Wait for embedding to complete
    echo "Waiting for embedding to complete (5 seconds)..."
    sleep 5

    echo -n "Searching for 'test document'... "
    search_response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d '{"query": "test document", "top_k": 5}' \
        "http://localhost:8000/api/v1/search")

    search_code=$(echo "$search_response" | tail -n 1)
    search_body=$(echo "$search_response" | sed '$d')

    if [ "$search_code" = "200" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $search_code)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo "  Response: $search_body"
    else
        echo -e "${RED}✗ FAIL${NC} (Expected HTTP 200, got $search_code)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "  Response: $search_body"
    fi
else
    echo -e "${RED}✗ SKIP${NC} (No document ID available)"
fi
echo ""

echo "5. Testing Generation (if OpenAI key available)"
echo "================================"
if [ -n "$OPENAI_API_KEY" ] || grep -q "OPENAI_API_KEY" ../../.env 2>/dev/null; then
    echo -n "Generating answer... "
    gen_response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d '{"question": "What is this document about?"}' \
        "http://localhost:8000/api/v1/generate")

    gen_code=$(echo "$gen_response" | tail -n 1)
    gen_body=$(echo "$gen_response" | sed '$d')

    if [ "$gen_code" = "200" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $gen_code)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo "  Response: $gen_body"
    else
        echo -e "${RED}✗ FAIL${NC} (Expected HTTP 200, got $gen_code)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo "  Response: $gen_body"
    fi
else
    echo -e "${RED}✗ SKIP${NC} (No OpenAI API key configured)"
fi
echo ""

echo "6. Testing Document Retrieval"
echo "================================"
if [ -n "$DOCUMENT_ID" ]; then
    test_endpoint "Get Document by ID" "http://localhost:8000/api/v1/documents/$DOCUMENT_ID" "200"
    test_endpoint "List Documents (with data)" "http://localhost:8000/api/v1/documents" "200"
else
    echo -e "${RED}✗ SKIP${NC} (No document ID available)"
fi
echo ""

echo "==================================="
echo "Test Results:"
echo "  Passed: $TESTS_PASSED"
echo "  Failed: $TESTS_FAILED"
echo "==================================="

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
