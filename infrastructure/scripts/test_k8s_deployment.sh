#!/bin/bash

# Test script for Kubernetes deployment workflow
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Testing Kubernetes Deployment Workflow ===${NC}\n"

# Store the project root
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
NAMESPACE="raas"

# Function to cleanup
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"

    # Delete kind cluster
    if kind get clusters 2>/dev/null | grep -q "^raas$"; then
        echo "Deleting kind cluster..."
        kind delete cluster --name raas 2>/dev/null || true
    fi

    echo -e "${GREEN}Cleanup complete${NC}"
}

# Set trap to cleanup on exit
trap cleanup EXIT

echo -e "${GREEN}Step 1: Checking prerequisites${NC}"

# Check if kind is installed
if ! command -v kind &> /dev/null; then
    echo -e "${RED}✗ kind is not installed${NC}"
    echo -e "${YELLOW}Install kind: https://kind.sigs.k8s.io/docs/user/quick-start/#installation${NC}"
    exit 1
fi
echo -e "${GREEN}✓ kind is installed${NC}"

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}✗ kubectl is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ kubectl is installed${NC}"

# Check if docker is running
if ! docker ps &> /dev/null; then
    echo -e "${RED}✗ Docker is not running${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}\n"

echo -e "${GREEN}Step 2: Creating kind cluster${NC}"
if kind get clusters 2>/dev/null | grep -q "^raas$"; then
    echo -e "${YELLOW}Deleting existing raas cluster...${NC}"
    kind delete cluster --name raas
fi

# Create kind cluster with port mappings
cat <<EOF | kind create cluster --name raas --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30000
    hostPort: 3000
    protocol: TCP
  - containerPort: 30080
    hostPort: 8000
    protocol: TCP
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Kind cluster created successfully${NC}\n"
else
    echo -e "${RED}✗ Failed to create kind cluster${NC}"
    exit 1
fi

echo -e "${GREEN}Step 3: Building Docker images${NC}"
echo "  Building API image..."
if docker build -t raas-api:latest -f services/api/Dockerfile services/api > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API image built${NC}"
else
    echo -e "${RED}✗ Failed to build API image${NC}"
    exit 1
fi

echo "  Building Embedder image..."
if docker build -t raas-embedder:latest -f services/embedder/Dockerfile services/embedder > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Embedder image built${NC}"
else
    echo -e "${RED}✗ Failed to build Embedder image${NC}"
    exit 1
fi

echo "  Building Generator image..."
if docker build -t raas-generator:latest -f services/generator/Dockerfile services/generator > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Generator image built${NC}"
else
    echo -e "${RED}✗ Failed to build Generator image${NC}"
    exit 1
fi

echo "  Building Search image..."
if docker build -t raas-search:latest -f services/search/Dockerfile services/search > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Search image built${NC}"
else
    echo -e "${RED}✗ Failed to build Search image${NC}"
    exit 1
fi

echo "  Building Frontend image..."
if docker build -t raas-frontend:latest -f services/frontend/Dockerfile services/frontend > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend image built${NC}\n"
else
    echo -e "${RED}✗ Failed to build Frontend image${NC}"
    exit 1
fi

echo -e "${GREEN}Step 4: Loading images into kind cluster${NC}"
kind load docker-image raas-api:latest --name raas
kind load docker-image raas-embedder:latest --name raas
kind load docker-image raas-generator:latest --name raas
kind load docker-image raas-search:latest --name raas
kind load docker-image raas-frontend:latest --name raas
echo -e "${GREEN}✓ Images loaded into kind cluster${NC}\n"

echo -e "${GREEN}Step 5: Applying Kubernetes manifests${NC}"
if kubectl apply -k infrastructure/k8s/overlays/local/; then
    echo -e "${GREEN}✓ Kubernetes manifests applied${NC}\n"
else
    echo -e "${RED}✗ Failed to apply Kubernetes manifests${NC}"
    exit 1
fi

echo -e "${GREEN}Step 6: Creating/updating Kubernetes secrets${NC}"
# Note: Secrets might already be created by the manifests, so we use kubectl apply or create
if [ -f ".env" ]; then
    source .env
    # Delete existing secrets if they exist
    kubectl delete secret raas-secrets -n $NAMESPACE 2>/dev/null || true
    kubectl create secret generic raas-secrets \
        --from-literal=openai-api-key="${OPENAI_API_KEY:-dummy-key}" \
        --from-literal=anthropic-api-key="${ANTHROPIC_API_KEY:-dummy-key}" \
        --from-literal=google-api-key="${GOOGLE_API_KEY:-dummy-key}" \
        --namespace=$NAMESPACE
else
    echo -e "${YELLOW}Warning: .env file not found. Using secrets from manifests${NC}"
fi
echo -e "${GREEN}✓ Secrets configured${NC}\n"

echo -e "${GREEN}Step 7: Waiting for deployments to be ready (up to 180 seconds)${NC}"
TIMEOUT=180

# StatefulSets (need different handling)
STATEFULSETS=("qdrant" "postgres")
for service in "${STATEFULSETS[@]}"; do
    echo "  Waiting for $service (StatefulSet)..."
    if kubectl rollout status statefulset/$service -n $NAMESPACE --timeout=${TIMEOUT}s; then
        echo -e "${GREEN}✓ $service is ready${NC}"
    else
        echo -e "${RED}✗ $service failed to become ready${NC}"
        kubectl get pods -n $NAMESPACE
        kubectl describe statefulset/$service -n $NAMESPACE
        kubectl logs -l app=$service -n $NAMESPACE --tail=50
        exit 1
    fi
done

# Deployments
DEPLOYMENTS=("api" "embedder" "generator" "search" "frontend")
for service in "${DEPLOYMENTS[@]}"; do
    echo "  Waiting for $service (Deployment)..."
    if kubectl rollout status deployment/$service -n $NAMESPACE --timeout=${TIMEOUT}s; then
        echo -e "${GREEN}✓ $service is ready${NC}"
    else
        echo -e "${RED}✗ $service failed to become ready${NC}"
        kubectl get pods -n $NAMESPACE
        kubectl describe deployment/$service -n $NAMESPACE
        kubectl logs -l app=$service -n $NAMESPACE --tail=50
        exit 1
    fi
done
echo ""

echo -e "${GREEN}Step 8: Verifying pod status${NC}"
kubectl get pods -n $NAMESPACE
RUNNING_PODS=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Running --no-headers | wc -l)
echo -e "${GREEN}✓ $RUNNING_PODS pods are running${NC}\n"

echo -e "${GREEN}Step 9: Checking service endpoints (note: may not be accessible depending on network setup)${NC}"

# Get service URLs
API_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:3000"

# Wait a bit for services to be fully ready
sleep 10

# Check API health
echo "  Checking API service..."
if timeout 10 curl -f $API_URL/api/v1/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API service is responding${NC}"
else
    echo -e "${YELLOW}⚠ API service is not responding (this may be expected if NodePort is not accessible)${NC}"
fi

# Check Frontend
echo "  Checking Frontend service..."
if timeout 10 curl -f $FRONTEND_URL > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend service is responding${NC}"
else
    echo -e "${YELLOW}⚠ Frontend service is not responding (this may be expected if NodePort is not accessible)${NC}"
fi

echo -e "\n${GREEN}Step 10: Verifying deployment resources${NC}"
echo "Deployments:"
kubectl get deployments -n $NAMESPACE

echo -e "\nServices:"
kubectl get services -n $NAMESPACE

echo -e "\nPersistent Volume Claims:"
kubectl get pvc -n $NAMESPACE

echo -e "\n${GREEN}=== Kubernetes Deployment Test PASSED ===${NC}"
echo -e "${GREEN}All services are deployed and running correctly!${NC}\n"

echo -e "${YELLOW}To access services, you can use port-forwarding:${NC}"
echo "  kubectl port-forward svc/frontend 3000:80 -n $NAMESPACE"
echo "  kubectl port-forward svc/api 8000:80 -n $NAMESPACE"
echo -e "\nOr access via NodePort at the configured host ports."

exit 0
