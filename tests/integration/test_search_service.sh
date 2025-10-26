#!/bin/bash
# Integration tests for search service

set -e

echo "=== Search Service Integration Tests ==="

BASE_URL="http://localhost:8003"

# Test 1: Health check
echo "Test 1: Health check"
response=$(curl -s ${BASE_URL}/api/v1/health)
if echo "$response" | grep -q '"status":"healthy"'; then
    echo "✓ Health check passed"
else
    echo "✗ Health check failed"
    exit 1
fi

# Test 2: Readiness check
echo "Test 2: Readiness check"
response=$(curl -s ${BASE_URL}/api/v1/ready)
if echo "$response" | grep -q '"status":"ready"'; then
    echo "✓ Readiness check passed"
else
    echo "✗ Readiness check failed"
    exit 1
fi

# Test 3: Vector search
echo "Test 3: Vector search"
response=$(curl -s -X POST ${BASE_URL}/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query":"Python programming","mode":"vector","top_k":5}')
if echo "$response" | grep -q '"query"'; then
    echo "✓ Vector search passed"
else
    echo "✗ Vector search failed"
    echo "Response: $response"
    exit 1
fi

# Test 4: Hybrid search
echo "Test 4: Hybrid search"
response=$(curl -s -X POST ${BASE_URL}/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query":"test","mode":"hybrid","top_k":10}')
if echo "$response" | grep -q '"total_results"'; then
    echo "✓ Hybrid search passed"
else
    echo "✗ Hybrid search failed"
    echo "Response: $response"
    exit 1
fi

# Test 5: Search with reranking disabled
echo "Test 5: Search with reranking disabled"
response=$(curl -s -X POST ${BASE_URL}/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query":"test","mode":"vector","top_k":5,"use_reranking":false}')
if echo "$response" | grep -q '"query"'; then
    echo "✓ Search without reranking passed"
else
    echo "✗ Search without reranking failed"
    exit 1
fi

# Test 6: Invalid query (empty)
echo "Test 6: Invalid query validation"
response=$(curl -s -w "\n%{http_code}" -X POST ${BASE_URL}/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query":"","mode":"vector","top_k":5}')
http_code=$(echo "$response" | tail -n1)
if [ "$http_code" = "422" ]; then
    echo "✓ Empty query validation passed"
else
    echo "✗ Empty query validation failed (expected 422, got $http_code)"
    exit 1
fi

echo ""
echo "=== All integration tests passed! ==="
