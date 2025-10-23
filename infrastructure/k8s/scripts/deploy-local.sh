#!/bin/bash
set -e

echo "🚀 Deploying RAAS to local Kubernetes..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster. Is Kind/Minikube running?"
    exit 1
fi

# Build images (optional - uncomment if needed)
# echo "📦 Building images..."
# docker build -t raas-api:latest ../../services/api
# docker build -t raas-embedder:latest ../../services/embedder
# docker build -t raas-generator:latest ../../services/generator
# docker build -t raas-frontend:latest ../../services/frontend

# Load images into Kind (if using Kind)
if kubectl config current-context | grep -q "kind"; then
    echo "📥 Loading images into Kind..."
    kind load docker-image raas-api:latest || echo "⚠️  Failed to load raas-api"
    kind load docker-image raas-embedder:latest || echo "⚠️  Failed to load raas-embedder"
    kind load docker-image raas-generator:latest || echo "⚠️  Failed to load raas-generator"
    kind load docker-image raas-frontend:latest || echo "⚠️  Failed to load raas-frontend"
fi

# Deploy with kustomize
echo "🎯 Deploying resources..."
kubectl apply -k ../overlays/local/

# Wait for deployments
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/api -n raas || true
kubectl wait --for=condition=available --timeout=300s deployment/embedder -n raas || true
kubectl wait --for=condition=available --timeout=300s deployment/frontend -n raas || true

# Show status
echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Status:"
kubectl get pods -n raas
echo ""
kubectl get svc -n raas
echo ""
echo "🌐 Access services:"
echo "  API: kubectl port-forward svc/api 8000:8000 -n raas"
echo "  Frontend: kubectl port-forward svc/frontend 3000:3000 -n raas"
echo ""
echo "📝 Logs:"
echo "  kubectl logs -f deployment/api -n raas"
