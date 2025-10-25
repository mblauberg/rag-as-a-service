#!/bin/bash
# Initialize Ollama with default models

set -e

OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"
DEFAULT_MODELS="${DEFAULT_MODELS:-llama3.2}"

echo "Waiting for Ollama to be ready..."
until curl -sf "$OLLAMA_URL/api/tags" > /dev/null; do
  echo "Ollama not ready, waiting..."
  sleep 5
done

echo "Ollama is ready. Pulling models..."

IFS=',' read -ra MODELS <<< "$DEFAULT_MODELS"
for model in "${MODELS[@]}"; do
  echo "Pulling model: $model"
  curl -X POST "$OLLAMA_URL/api/pull" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"$model\"}" \
    --max-time 600
  echo "Model $model pulled successfully"
done

echo "All models initialized"
