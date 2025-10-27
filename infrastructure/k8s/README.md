# Kubernetes Deployment for RAAS

This directory contains Kubernetes manifests for deploying the RAAS (Retrieval-Augmented Generation as a Service) platform.

## Architecture

- **Base**: Environment-agnostic manifests in `base/`
- **Overlays**: Environment-specific configs
  - `local/` - Kind/Minikube
  - `production/` - Cloud (GCP, AWS, Azure)

## Services

| Service | Type | Replicas (local/prod) | Port | Description |
|---------|------|----------------------|------|-------------|
| postgres | StatefulSet | 1/1 | 5432 | PostgreSQL database |
| qdrant | StatefulSet | 1/1 | 6333, 6334 | Vector database |
| api | Deployment | 1/3 | 8000 | FastAPI gateway |
| embedder | Deployment | 1/3 | 8001 | Embedding service |
| generator | Deployment | 1/2 | 8002 | Text generation |
| search | Deployment | 1/2 | 8003 | Search service |
| frontend | Deployment | 1/2 | 3000 | React SPA |

## Prerequisites

### Local Development

```bash
# Install Kind
brew install kind

# Or Minikube
brew install minikube

# Install kubectl
brew install kubectl

# Install Kustomize (optional - kubectl has built-in support)
brew install kustomize
```

### Production

- Kubernetes cluster (GKE, EKS, AKS)
- kubectl configured with cluster credentials
- NGINX Ingress Controller installed
- Container registry (GCR, ECR, ACR)

## Quick Start

### Local Deployment (Kind)

**Option 1: Automated (Recommended)**

```bash
./infrastructure/scripts/setup-kind-full.sh
```

Creates cluster, builds images, installs ingress, deploys services.

**Option 2: Manual Setup**

**1. Create Kind cluster:**
```bash
kind create cluster --name raas-cluster --config infrastructure/kind/kind-config.yaml
```

**2. Load images into Kind:**
```bash
# Build images first (from project root)
docker build -t raas-api:latest ./services/api
docker build -t raas-embedder:latest ./services/embedder
docker build -t raas-generator:latest ./services/generator
docker build -t raas-frontend:latest ./services/frontend

# Load into Kind
kind load docker-image raas-api:latest --name raas-cluster
kind load docker-image raas-embedder:latest --name raas-cluster
kind load docker-image raas-generator:latest --name raas-cluster
kind load docker-image raas-frontend:latest --name raas-cluster
```

**3. Install NGINX Ingress:**
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Wait for ingress controller to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s
```

**4. Deploy RAAS:**
```bash
kubectl apply -k infrastructure/k8s/overlays/local/
```

**5. Verify deployment:**
```bash
kubectl get pods -n raas
kubectl get svc -n raas
kubectl get ingress -n raas
```

**6. Access services:**
```bash
# Port-forward to access locally
kubectl port-forward svc/api 8000:8000 -n raas &
kubectl port-forward svc/frontend 3000:80 -n raas &

# Or use Ingress (requires /etc/hosts entry)
echo "127.0.0.1 raas.local" | sudo tee -a /etc/hosts
curl http://raas.local/api/v1/health
```

### Production Deployment

**1. Update production configuration:**

Edit `overlays/production/kustomization.yaml`:
- Update image registry paths
- Update image tags
- Update frontend API URL

Edit `overlays/production/secret-patches.yaml`:
- Update PostgreSQL password
- Update DATABASE_URL

**2. Push images to registry:**
```bash
docker tag raas-api:latest gcr.io/your-project/raas-api:v1.0.0
docker push gcr.io/your-project/raas-api:v1.0.0

# Repeat for all services
```

**3. Deploy to production:**
```bash
kubectl apply -k infrastructure/k8s/overlays/production/
```

**4. Monitor rollout:**
```bash
kubectl rollout status deployment/api -n raas
kubectl rollout status deployment/embedder -n raas
kubectl rollout status deployment/frontend -n raas
kubectl rollout status deployment/generator -n raas
```

**5. Verify:**
```bash
kubectl get pods -n raas -o wide
kubectl get hpa -n raas
kubectl get ingress -n raas
```

## Common Operations

### View Logs

```bash
# API logs
kubectl logs -f deployment/api -n raas

# Embedder logs
kubectl logs -f deployment/embedder -n raas

# All pods
kubectl logs -f -l app=api -n raas --all-containers=true
```

### Scale Services

```bash
# Manual scaling
kubectl scale deployment/api --replicas=5 -n raas

# HPA will automatically scale based on CPU/memory
kubectl get hpa -n raas -w
```

### Update Image

```bash
# Update to new version
kubectl set image deployment/api api=raas-api:v2 -n raas

# Monitor rollout
kubectl rollout status deployment/api -n raas

# Rollback if needed
kubectl rollout undo deployment/api -n raas
```

### Restart Service

```bash
kubectl rollout restart deployment/api -n raas
```

### Access Database

```bash
# PostgreSQL
kubectl exec -it statefulset/postgres -n raas -- psql -U raasuser -d raasdb

# Qdrant (port-forward)
kubectl port-forward svc/qdrant 6333:6333 -n raas
# Open http://localhost:6333/dashboard
```

### Debug Pod Issues

```bash
# Describe pod
kubectl describe pod <pod-name> -n raas

# Get events
kubectl get events -n raas --sort-by='.lastTimestamp'

# Exec into pod
kubectl exec -it <pod-name> -n raas -- /bin/sh

# Check resource usage
kubectl top pods -n raas
kubectl top nodes
```

## Rollout & Rollback

### Deployment Strategy

All Deployments use `RollingUpdate`:
- `maxUnavailable: 1` - At most 1 pod down during update
- `maxSurge: 1` - At most 1 extra pod during update
- `revisionHistoryLimit: 10` - Keep last 10 revisions

### Rollout Commands

```bash
# View rollout history
kubectl rollout history deployment/api -n raas

# Check rollout status
kubectl rollout status deployment/api -n raas

# Pause rollout
kubectl rollout pause deployment/api -n raas

# Resume rollout
kubectl rollout resume deployment/api -n raas
```

### Rollback Commands

```bash
# Rollback to previous version
kubectl rollout undo deployment/api -n raas

# Rollback to specific revision
kubectl rollout undo deployment/api --to-revision=3 -n raas

# Verify rollback
kubectl rollout status deployment/api -n raas
```

## Health Checks

All services include liveness and readiness probes:

| Service | Liveness | Readiness | Initial Delay (L/R) |
|---------|----------|-----------|---------------------|
| postgres | pg_isready | pg_isready | 10s / 5s |
| qdrant | HTTP / :6333 | HTTP / :6333 | 10s / 15s |
| api | HTTP /api/v1/health :8000 | HTTP /api/v1/health/ready :8000 | 15s / 20s |
| embedder | HTTP /health :8001 | HTTP /ready :8001 | 20s / 30s |
| generator | HTTP /health :8002 | HTTP /health/ready :8002 | 15s / 20s |
| frontend | HTTP / :80 | HTTP / :80 | 10s / 5s |

## Monitoring

### Built-in

```bash
# Pod status
kubectl get pods -n raas -w

# Resource usage
kubectl top pods -n raas
kubectl top nodes

# HPA metrics
kubectl get hpa -n raas -w

# Events
kubectl get events -n raas --watch
```

### Prometheus (Optional)

Install Prometheus operator and add ServiceMonitor resources for metrics collection.

## Troubleshooting

### Pods in CrashLoopBackOff

```bash
# Check logs
kubectl logs <pod-name> -n raas --previous

# Check events
kubectl describe pod <pod-name> -n raas

# Common causes:
# - Database not ready (check postgres pod)
# - Missing environment variables (check configmap/secret)
# - Health probe failures (check probe endpoints)
```

### ImagePullBackOff

```bash
# Check image name/tag in deployment
kubectl describe deployment/api -n raas

# Local (Kind): Ensure image loaded
kind load docker-image raas-api:latest --name raas-cluster

# Production: Check registry authentication
kubectl get secret -n raas
```

### Service Not Accessible

```bash
# Check service
kubectl get svc -n raas
kubectl describe svc/api -n raas

# Check endpoints
kubectl get endpoints -n raas

# Check ingress
kubectl get ingress -n raas
kubectl describe ingress/raas-ingress -n raas
```

### PVC Pending

```bash
# Check PVC status
kubectl get pvc -n raas
kubectl describe pvc/postgres-data -n raas

# Local: Ensure storage class exists
kubectl get storageclass

# Kind: Install local-path provisioner
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/master/deploy/local-path-storage.yaml
```

### HPA Not Scaling

```bash
# Check metrics server installed
kubectl get deployment metrics-server -n kube-system

# Install if missing (Kind)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Check HPA status
kubectl describe hpa/api-hpa -n raas
```

## Cleanup

### Local

```bash
# Delete all resources
kubectl delete -k infrastructure/k8s/overlays/local/

# Or delete namespace (removes everything)
kubectl delete namespace raas

# Delete Kind cluster
kind delete cluster --name raas-cluster
```

### Production

```bash
# Delete application (keeps PVCs)
kubectl delete -k infrastructure/k8s/overlays/production/

# Delete including PVCs
kubectl delete namespace raas
```

## Directory Structure

```
infrastructure/k8s/
├── base/                           # Base manifests
│   ├── namespace.yaml             # raas namespace
│   ├── postgres/                  # PostgreSQL
│   │   ├── statefulset.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   ├── secret.yaml
│   │   └── pvc.yaml
│   ├── qdrant/                    # Qdrant
│   │   ├── statefulset.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   └── pvc.yaml
│   ├── api/                       # API service
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   ├── hpa.yaml
│   │   └── pvc.yaml
│   ├── embedder/                  # Embedder
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   ├── hpa.yaml
│   │   └── pvc.yaml
│   ├── frontend/                  # Frontend
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   ├── generator/                 # Generator
│   ├── search/                    # Search service
│   ├── ingress.yaml              # Ingress controller
│   └── kustomization.yaml        # Base kustomization
├── overlays/
│   ├── local/                     # Local dev
│   │   ├── kustomization.yaml
│   │   ├── replica-patches.yaml
│   │   ├── resource-patches.yaml
│   │   ├── storage-patches.yaml
│   │   └── hpa-patches.yaml
│   └── production/                # Production
│       ├── kustomization.yaml
│       ├── replica-patches.yaml
│       ├── imagepull-patches.yaml
│       └── secret-patches.yaml
└── README.md
```

## Security Considerations

### Current

- Secrets for passwords and tokens
- Resource limits
- Network isolation via ClusterIP
- Health probes

### Future

- NetworkPolicies
- RBAC
- Pod Security Standards
- Image scanning
- Encrypted secrets

## Type I Project Requirements

This scaffolding satisfies INFS3208 Type I requirements:

- ✅ Microservice architecture (7 services)
- ✅ Containerization (all services in containers)
- ✅ Scalability (HPA on API, Embedder, Generator)
- ✅ Reliability (multiple replicas, health probes)
- ✅ Load balancing (K8s Service + Ingress)
- ✅ Orchestration (Kubernetes)
- ✅ Rollout and rollback (RollingUpdate strategy)

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review root README: `../../README.md`
3. Check Kubernetes logs: `kubectl logs -f <pod-name> -n raas`
4. Run verification script: `./infrastructure/scripts/verify-type1-requirements.sh`
