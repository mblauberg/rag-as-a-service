#!/bin/bash

set -e

BASE_URL="http://localhost:8000/api/v1"

echo "Testing Generation Flow..."

# 1. Check if Generator models are available
echo "1. Listing available models..."
MODELS=$(curl -s "$BASE_URL/models")
echo "Available models: $MODELS"

# 2. Upload a test document
echo "2. Uploading test document..."
DOC_ID=$(curl -s -X POST "$BASE_URL/documents" \
  -F "file=@tests/fixtures/sample.pdf" \
  -F "title=Test Document" | jq -r '.document_id')
echo "Uploaded document: $DOC_ID"

# Wait for embedding
sleep 5

# 3. Search with generation
echo "3. Searching with generation..."
SEARCH_RESULT=$(curl -s -X POST "$BASE_URL/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this document about?", "limit": 5, "model": "llama3.2"}')

SUMMARY=$(echo "$SEARCH_RESULT" | jq -r '.summary')
MODEL_USED=$(echo "$SEARCH_RESULT" | jq -r '.model_used')

echo "Summary: $SUMMARY"
echo "Model used: $MODEL_USED"

# 4. Verify summary has citations
if echo "$SUMMARY" | grep -q "\[1\]"; then
  echo "✓ Summary contains citations"
else
  echo "✗ Summary missing citations"
  exit 1
fi

echo "✓ All generation tests passed!"
