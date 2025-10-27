#!/bin/bash
set -e

echo "========================================="
echo "RAAS Kubernetes Cluster Setup for Type I Project"
echo "========================================="

# Configuration
CLUSTER_NAME="raas-cluster"
NAMESPACE="raas"

echo ""
echo "Step 1: Deleting existing Kind cluster (if any)..."
kind delete cluster --name $CLUSTER_NAME 2>/dev/null || echo "No existing cluster to delete"

echo ""
echo "Step 2: Creating new Kind cluster with ingress port mappings..."
kind create cluster --name $CLUSTER_NAME --config infrastructure/kind/kind-config.yaml

echo ""
echo "Step 3: Installing NGINX Ingress Controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

echo "Waiting for NGINX Ingress Controller to be ready..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s

echo ""
echo "Step 4: Installing metrics-server for HPA..."
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Patch metrics-server for Kind (it needs --kubelet-insecure-tls)
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'

echo "Waiting for metrics-server to be ready..."
kubectl wait --namespace kube-system \
  --for=condition=ready pod \
  --selector=k8s-app=metrics-server \
  --timeout=90s

echo ""
echo "Step 5: Creating RAAS namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "Step 6: Building and loading Docker images into Kind..."
# Build all images
echo "Building API service..."
docker build -t raas-api:latest -f services/api/Dockerfile services/api

echo "Building Embedder service..."
docker build -t raas-embedder:latest -f services/embedder/Dockerfile services/embedder

echo "Building Generator service..."
docker build -t raas-generator:latest -f services/generator/Dockerfile services/generator

echo "Building Search service..."
docker build -t raas-search:latest -f services/search/Dockerfile services/search

echo "Building Frontend..."
docker build -t raas-frontend:latest -f services/frontend/Dockerfile services/frontend

# Load images into Kind
echo "Loading images into Kind cluster..."
kind load docker-image raas-api:latest --name $CLUSTER_NAME
kind load docker-image raas-embedder:latest --name $CLUSTER_NAME
kind load docker-image raas-generator:latest --name $CLUSTER_NAME
kind load docker-image raas-search:latest --name $CLUSTER_NAME
kind load docker-image raas-frontend:latest --name $CLUSTER_NAME

echo ""
echo "Step 7: Deploying RAAS application..."
kubectl apply -k infrastructure/k8s/overlays/local/

echo ""
echo "Step 8: Waiting for deployments to be ready..."
echo "Waiting for PostgreSQL..."
kubectl wait --namespace $NAMESPACE \
  --for=condition=ready pod \
  --selector=app=postgres \
  --timeout=120s

echo "Waiting for Qdrant..."
kubectl wait --namespace $NAMESPACE \
  --for=condition=ready pod \
  --selector=app=qdrant \
  --timeout=120s

echo "Waiting for API..."
kubectl rollout status deployment/api -n $NAMESPACE --timeout=120s

echo "Waiting for Embedder..."
kubectl rollout status deployment/embedder -n $NAMESPACE --timeout=120s

echo "Waiting for Generator..."
kubectl rollout status deployment/generator -n $NAMESPACE --timeout=120s

echo "Waiting for Search..."
kubectl rollout status deployment/search -n $NAMESPACE --timeout=120s

echo "Waiting for Frontend..."
kubectl rollout status deployment/frontend -n $NAMESPACE --timeout=120s

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Cluster Information:"
kubectl cluster-info --context kind-$CLUSTER_NAME
echo ""
echo "Deployed Pods:"
kubectl get pods -n $NAMESPACE
echo ""
echo "Deployed Services:"
kubectl get svc -n $NAMESPACE
echo ""
echo "Ingress Status:"
kubectl get ingress -n $NAMESPACE
echo ""
echo "HPA Status:"
kubectl get hpa -n $NAMESPACE
echo ""
echo "========================================="
echo "Access Points:"
echo "  Frontend: http://localhost/"
echo "  API: http://localhost/api/v1/health"
echo "  Qdrant Dashboard: kubectl port-forward -n $NAMESPACE svc/qdrant 6333:6333"
echo "========================================="
echo ""
echo "Type I Requirements Checklist:"
echo "  ✅ Frontend: Interactive UI (React)"
echo "  ✅ Backend: Database (PostgreSQL + Qdrant)"
echo "  ✅ Microservices: Containerized services"
echo "  ✅ Orchestration: Kubernetes"
echo "  ✅ Load Balancing: NGINX Ingress"
echo "  ✅ Scalability: HPA configured"
echo "  ✅ Reliability: Multiple replicas"
echo "  ✅ Rollout/Rollback: RollingUpdate strategy"
echo ""
echo "Next steps:"
echo "  1. Test application: http://localhost/"
echo "  2. Upload documents to meet 10,000+ records requirement"
echo "  3. Test HPA: kubectl get hpa -n $NAMESPACE -w"
echo "  4. Test rollout: See infrastructure/scripts/test-rollout.sh"
echo "  5. Test reliability: kubectl delete pod <pod-name> -n $NAMESPACE"
echo ""
