#!/bin/bash

set -e

echo "=== Multi-Provider Integration Test ==="

# Start services
echo "Starting services..."
cd infrastructure/docker-compose
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services..."
sleep 10

# Test 1: List models from cloud providers
echo "Test 1: List models from configured providers"
MODELS=$(curl -s http://localhost:8002/models)
echo "$MODELS" | jq -e '.models | length > 0' || { echo "FAIL: No models returned"; exit 1; }
echo "✓ Models endpoint working"

# Test 2: Verify enhanced schema
echo "Test 2: Verify enhanced model schema"
echo "$MODELS" | jq -e '.models[0] | has("display_name")' || { echo "FAIL: Missing display_name"; exit 1; }
echo "$MODELS" | jq -e '.models[0] | has("provider")' || { echo "FAIL: Missing provider"; exit 1; }
echo "$MODELS" | jq -e '.models[0] | has("description")' || { echo "FAIL: Missing description"; exit 1; }
echo "✓ Enhanced schema present"

# Test 3: Generate summary
echo "Test 3: Generate summary with default model"
MODEL_NAME=$(echo "$MODELS" | jq -r '.models[0].name')
RESPONSE=$(curl -s -X POST http://localhost:8002/generate \
  -H "Content-Type: application/json" \
  -d "{\"model\": \"$MODEL_NAME\", \"prompt\": \"test query\", \"context\": \"test context\"}")
echo "$RESPONSE" | jq -e '.summary' || { echo "FAIL: No summary generated"; exit 1; }
echo "✓ Generation working"

# Test 4: Frontend models endpoint
echo "Test 4: Frontend can fetch models via API"
API_MODELS=$(curl -s http://localhost:8000/api/v1/models)
echo "$API_MODELS" | jq -e '.models | length > 0' || { echo "FAIL: API models endpoint broken"; exit 1; }
echo "✓ API passthrough working"

# Cleanup
echo "Cleaning up..."
docker-compose down

echo "=== All tests passed ==="
