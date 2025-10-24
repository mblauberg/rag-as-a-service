# Kubernetes Scaffolding Design

**Date:** October 24, 2025
**Status:** Design Approved
**Type:** Type I - Highly Scalable and Available Application

## Overview

This document describes the Kubernetes manifest scaffolding for the RAAS (Retrieval-Augmented Generation as a Service) platform. The scaffolding provides production-ready manifests for orchestrating all microservices while supporting both local development and production deployments.

## Purpose

- **Scaffolding**: Create K8s manifest structure before actual deployment
- **Flexibility**: Support both local (Kind/Minikube) and production (GCP/AWS) environments
- **Type I Compliance**: Meet INFS3208 Type I project requirements for orchestration, scalability, and reliability
- **Future-ready**: Easy to update as services evolve

## Design Decisions

### 1. Directory Structure

**Pattern:** Service-per-directory (matches existing generator/ollama structure)

```
infrastructure/k8s/
├── base/                                # Base manifests (environment-agnostic)
│   ├── namespace.yaml                   # raas namespace
│   ├── postgres/                        # PostgreSQL StatefulSet
│   │   ├── statefulset.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   ├── secret.yaml
│   │   └── pvc.yaml
│   ├── qdrant/                          # Qdrant vector database
│   │   ├── statefulset.yaml
│   │   ├── service.yaml
│   │   ├── pvc.yaml
│   │   └── configmap.yaml
│   ├── api/                             # API gateway service
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   ├── hpa.yaml
│   │   └── pvc.yaml
│   ├── embedder/                        # Embedding generation service
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   ├── hpa.yaml
│   │   └── pvc.yaml
│   ├── frontend/                        # React frontend
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   ├── generator/                       # Already exists
│   ├── ollama/                          # Already exists
│   ├── ingress.yaml                     # Ingress controller config
│   └── kustomization.yaml               # Base kustomization
├── overlays/
│   ├── local/                           # Local development patches
│   │   ├── kustomization.yaml
│   │   ├── namespace-patch.yaml
│   │   └── resource-patches/
│   └── production/                      # Production patches
│       ├── kustomization.yaml
│       ├── namespace-patch.yaml
│       └── resource-patches/
└── README.md
```

**Rationale:**
- Modular: Each service is self-contained and easy to locate
- Consistent: Follows existing pattern (generator, ollama)
- Scalable: Easy to add new services without restructuring

### 2. Deployment Architecture

#### Stateful Services (StatefulSets)

**PostgreSQL:**
- **Type:** StatefulSet with 1 replica
- **Storage:** PVC with 10Gi (local: 2Gi)
- **Service:** Headless ClusterIP for stable network identity
- **Probes:**
  - Liveness: `pg_isready -U raasuser -d raasdb`
  - Readiness: Same as liveness
- **Resources:**
  - Requests: 500m CPU, 1Gi RAM
  - Limits: 1000m CPU, 2Gi RAM
- **Init:** ConfigMap with SQL migrations mounted at `/docker-entrypoint-initdb.d`

**Qdrant:**
- **Type:** StatefulSet with 1 replica
- **Storage:** PVC with 20Gi (local: 5Gi)
- **Service:** ClusterIP on ports 6333 (HTTP) and 6334 (gRPC)
- **Probes:**
  - Liveness: HTTP GET / on port 6333
  - Readiness: HTTP GET / on port 6333
- **Resources:**
  - Requests: 1000m CPU, 2Gi RAM
  - Limits: 2000m CPU, 4Gi RAM

**Rationale:** StatefulSets provide:
- Stable pod identities (postgres-0, qdrant-0)
- Ordered deployment and scaling
- Persistent storage that survives pod restarts
- Required for databases and stateful workloads

#### Stateless Services (Deployments)

**API Service:**
- **Replicas:** 2 (local: 1)
- **Service:** ClusterIP on port 8000
- **Probes:**
  - Liveness: HTTP GET /api/v1/health
  - Readiness: HTTP GET /api/v1/health/ready
  - Initial delay: 15s (liveness), 20s (readiness)
- **Resources:**
  - Requests: 500m CPU, 1Gi RAM
  - Limits: 2000m CPU, 2Gi RAM
- **Storage:** PVC 5Gi for uploads (ReadWriteMany if available)
- **HPA:** Scale 2-10 replicas based on 70% CPU, 80% memory
- **Environment:** ConfigMap + Secret refs

**Embedder Service:**
- **Replicas:** 2 (local: 1)
- **Service:** ClusterIP on port 8001
- **Probes:**
  - Liveness: HTTP GET /health (initial delay: 20s)
  - Readiness: HTTP GET /ready (initial delay: 30s, failure threshold: 6)
- **Resources:**
  - Requests: 1000m CPU, 2Gi RAM
  - Limits: 3000m CPU, 4Gi RAM
- **Storage:** PVC 10Gi for model cache
- **HPA:** Scale 2-8 replicas based on 70% CPU, 80% memory
- **Note:** Longer readiness delay to allow model loading

**Frontend:**
- **Replicas:** 2 (local: 1)
- **Service:** ClusterIP on port 3000
- **Probes:**
  - Liveness: HTTP GET / on port 3000 (initial delay: 10s)
  - Readiness: HTTP GET / on port 3000 (initial delay: 5s)
- **Resources:**
  - Requests: 100m CPU, 256Mi RAM
  - Limits: 500m CPU, 512Mi RAM
- **Environment:** ConfigMap with VITE_API_URL

**Generator & Ollama:**
- Already implemented with proper structure
- Will remain as-is

### 3. Networking

#### Service Discovery (ClusterIP)

All internal communication uses Kubernetes DNS:

```
postgres:5432              # PostgreSQL
qdrant:6333               # Qdrant HTTP
qdrant:6334               # Qdrant gRPC
api:8000                  # API service
embedder:8001             # Embedder
generator:8002            # Generator
ollama:11434              # Ollama
frontend:3000             # Frontend
```

Fully qualified DNS format: `<service>.<namespace>.svc.cluster.local`

#### External Access (Ingress)

**Single Ingress with path-based routing:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: raas-ingress
  namespace: raas
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$2
spec:
  ingressClassName: nginx
  rules:
  - http:
      paths:
      - path: /api(/|$)(.*)
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 8000
      - path: /()(.*)
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000
```

**Routing:**
- `/api/*` → API service (port 8000)
- `/*` → Frontend service (port 3000)

**SSL/TLS:** Can be added via cert-manager in production

### 4. Configuration Management

#### Secrets

PostgreSQL credentials stored in K8s Secret:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: raas
type: Opaque
stringData:
  POSTGRES_DB: raasdb
  POSTGRES_USER: raasuser
  POSTGRES_PASSWORD: raaspass  # Override in production
  DATABASE_URL: postgresql+asyncpg://raasuser:raaspass@postgres:5432/raasdb
```

**Production:** Use stronger passwords, potentially external secret management (GCP Secret Manager, AWS Secrets Manager)

#### ConfigMaps

Each service has a ConfigMap for environment variables:

**API ConfigMap:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
  namespace: raas
data:
  QDRANT_URL: "http://qdrant:6333"
  EMBEDDER_URL: "http://embedder:8001"
  GENERATOR_URL: "http://generator:8002"
  UPLOAD_DIR: "/app/uploads"
  MAX_UPLOAD_SIZE: "104857600"
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
  API_WORKERS: "4"
  CORS_ORIGINS: '["http://localhost:3000"]'
  LOG_LEVEL: "INFO"
```

**Embedder ConfigMap:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: embedder-config
  namespace: raas
data:
  QDRANT_URL: "http://qdrant:6333"
  MODEL_NAME: "BAAI/bge-m3"
  MODEL_DIMENSION: "1024"
  BATCH_SIZE: "16"
  MAX_SEQUENCE_LENGTH: "512"
  API_HOST: "0.0.0.0"
  API_PORT: "8001"
  API_WORKERS: "2"
  COLLECTION_NAME: "documents"
  LOG_LEVEL: "INFO"
```

**Frontend ConfigMap:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: frontend-config
  namespace: raas
data:
  VITE_API_URL: "http://localhost:8000"  # Override in production
```

**Injection:**
```yaml
spec:
  containers:
  - name: api
    envFrom:
    - configMapRef:
        name: api-config
    - secretRef:
        name: postgres-secret
```

### 5. Scalability & High Availability

#### Horizontal Pod Autoscaler (HPA)

**API HPA:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: raas
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Embedder HPA:**
- minReplicas: 2, maxReplicas: 8
- CPU: 70%, Memory: 80%

**Generator HPA:**
- Already implemented

**Local overlay:** Set minReplicas=1, maxReplicas=2 for development

#### Load Balancing

Kubernetes Services provide built-in load balancing:
- Round-robin traffic distribution across pod replicas
- Automatic endpoint updates as pods scale
- Health check integration (only send to ready pods)

#### Reliability

**Multiple replicas:**
- API: 2+ replicas (survives 1 pod failure)
- Embedder: 2+ replicas
- Frontend: 2+ replicas

**Health probes:**
- Liveness: Restart unhealthy pods
- Readiness: Don't send traffic until ready

**Pod anti-affinity (optional):**
Can be added to spread replicas across nodes:
```yaml
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - api
        topologyKey: kubernetes.io/hostname
```

### 6. Deployment Strategy (Rollout & Rollback)

#### Rolling Updates

All Deployments use `RollingUpdate` strategy:

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1  # At most 1 pod down during update
      maxSurge: 1        # At most 1 extra pod during update
  revisionHistoryLimit: 10  # Keep last 10 revisions for rollback
```

**Benefits:**
- Zero-downtime deployments
- New pods verified healthy before old pods terminated
- Gradual rollout minimizes risk

#### Rollout Commands

```bash
# Update image to new version
kubectl set image deployment/api api=raas-api:v2 -n raas

# Monitor rollout progress
kubectl rollout status deployment/api -n raas

# View rollout history
kubectl rollout history deployment/api -n raas

# Pause rollout (if issues detected)
kubectl rollout pause deployment/api -n raas

# Resume rollout
kubectl rollout resume deployment/api -n raas
```

#### Rollback Commands

```bash
# Rollback to previous version
kubectl rollout undo deployment/api -n raas

# Rollback to specific revision
kubectl rollout undo deployment/api --to-revision=3 -n raas

# Verify rollback completed
kubectl rollout status deployment/api -n raas

# Check current revision
kubectl rollout history deployment/api -n raas
```

**Revision tracking:** Each deployment keeps last 10 revisions in history for emergency rollback.

### 7. Storage Management

#### Persistent Volume Claims

**PostgreSQL PVC:**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data
  namespace: raas
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi  # Local: 2Gi
  storageClassName: standard  # Local: local-path
```

**Qdrant PVC:**
- Size: 20Gi (local: 5Gi)
- AccessMode: ReadWriteOnce

**API Uploads PVC:**
- Size: 5Gi (local: 2Gi)
- AccessMode: ReadWriteMany (if supported), else ReadWriteOnce

**Embedder Model Cache PVC:**
- Size: 10Gi (local: 5Gi)
- AccessMode: ReadWriteOnce

**Storage Classes:**
- **Local:** `local-path` (Kind), `standard` (Minikube)
- **Production:** `standard-rwo` (GCP), `gp2` (AWS)

#### Data Persistence

- StatefulSets maintain PVC bindings across pod restarts
- PVCs survive pod deletion (manual deletion required)
- Backup strategy can be implemented via CronJobs

### 8. Environment-Specific Configuration

#### Kustomize Overlays

**Base:** Contains common configuration for all environments

**Local Overlay (`overlays/local/kustomization.yaml`):**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: raas

bases:
- ../../base

patchesStrategicMerge:
- replica-patches.yaml
- resource-patches.yaml
- storage-patches.yaml

images:
- name: raas-api
  newTag: latest
- name: raas-embedder
  newTag: latest
- name: raas-frontend
  newTag: latest
- name: raas-generator
  newTag: latest

configMapGenerator:
- name: frontend-config
  behavior: merge
  literals:
  - VITE_API_URL=http://localhost:8000
```

**Patches for local:**
- Replicas: 1 for all services
- Resources: Lower limits (512Mi-1Gi RAM)
- ImagePullPolicy: Never
- Storage: Smaller sizes (2-5Gi)
- StorageClassName: local-path

**Production Overlay (`overlays/production/kustomization.yaml`):**
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: raas

bases:
- ../../base

patchesStrategicMerge:
- replica-patches.yaml
- resource-patches.yaml
- storage-patches.yaml
- secret-patches.yaml

images:
- name: raas-api
  newName: gcr.io/project-id/raas-api
  newTag: v1.0.0
- name: raas-embedder
  newName: gcr.io/project-id/raas-embedder
  newTag: v1.0.0
- name: raas-frontend
  newName: gcr.io/project-id/raas-frontend
  newTag: v1.0.0

configMapGenerator:
- name: frontend-config
  behavior: merge
  literals:
  - VITE_API_URL=https://raas.example.com
```

**Patches for production:**
- Replicas: 2-3 for all services
- Resources: Production-grade limits (2-4Gi RAM)
- ImagePullPolicy: Always
- Storage: Larger sizes (10-20Gi)
- StorageClassName: standard-rwo
- Secrets: Strong passwords

#### Deployment Commands

**Local:**
```bash
# Deploy to Kind/Minikube
kubectl apply -k infrastructure/k8s/overlays/local/

# Verify deployment
kubectl get pods -n raas
kubectl get svc -n raas
kubectl get ingress -n raas
```

**Production:**
```bash
# Deploy to production cluster
kubectl apply -k infrastructure/k8s/overlays/production/

# Monitor rollout
kubectl rollout status deployment/api -n raas
kubectl rollout status deployment/embedder -n raas
kubectl rollout status deployment/frontend -n raas

# Verify
kubectl get pods -n raas -o wide
```

### 9. Health Checks Summary

| Service | Liveness Probe | Readiness Probe | Initial Delay (L/R) |
|---------|---------------|-----------------|---------------------|
| PostgreSQL | `pg_isready -U raasuser` | Same as liveness | 10s / 5s |
| Qdrant | HTTP GET / :6333 | HTTP GET / :6333 | 10s / 15s |
| API | HTTP GET /api/v1/health :8000 | HTTP GET /api/v1/health/ready :8000 | 15s / 20s |
| Embedder | HTTP GET /health :8001 | HTTP GET /ready :8001 | 20s / 30s |
| Frontend | HTTP GET / :3000 | HTTP GET / :3000 | 10s / 5s |
| Generator | HTTP GET /health :8002 | HTTP GET /ready :8002 | 10s / 15s |
| Ollama | curl http://localhost:11434/api/tags | Same | 30s / 30s |

**Rationale for different delays:**
- **PostgreSQL/Frontend:** Fast startup, short delays
- **API:** Needs DB connection, moderate delay
- **Embedder:** Must download/load model, longest delay (30s+)
- **Qdrant/Ollama:** Medium startup time

### 10. Type I Project Compliance

This design satisfies all INFS3208 Type I requirements:

| Requirement | Implementation | Marks |
|-------------|---------------|-------|
| **Frontend** | React SPA with Tailwind CSS, served via NGINX | 1 |
| **Backend Database** | PostgreSQL (relational), Qdrant (vector database) | 1 |
| **4+ Functionalities** | Upload, Search, Generate, Document Management, Vector Search | 1 |
| **Microservices + Containers** | 7 services (API, Embedder, Generator, Frontend, Postgres, Qdrant, Ollama), all containerized | 2 |
| **Scalability** | HPA on API, Embedder, Generator (2-10 replicas based on CPU/memory) | 1 |
| **Reliability** | Multiple replicas, health probes, StatefulSets for data, survives pod failures | 1 |
| **Load Balancing** | K8s Service ClusterIP (built-in round-robin), Ingress controller | 1 |
| **Orchestration** | Kubernetes with Deployments, StatefulSets, Services, Ingress, HPA, ConfigMaps, Secrets | 3 |
| **Rollout & Rollback** | RollingUpdate strategy, revision history, kubectl rollout commands | 1 |
| **Data Size** | Supports 10,000+ documents via PostgreSQL + Qdrant vector storage | 1 |
| **Data Storage** | PostgreSQL (relational) + Qdrant (vectors) with persistent volumes | 1 |
| **Innovation** | RAG system with semantic search, embeddings, reranking, hybrid search, generation | 3 |

**Total Potential: 15/15 marks**

### 11. Future Enhancements

**Phase 1 (Optional):**
- NetworkPolicies for pod-to-pod security
- PodDisruptionBudgets for voluntary disruptions
- Resource quotas per namespace

**Phase 2 (Advanced):**
- ServiceMonitor for Prometheus metrics
- Grafana dashboards for monitoring
- External secrets via GCP Secret Manager
- Multi-region deployment
- Service mesh (Istio) for advanced traffic management

**Phase 3 (Production Hardening):**
- RBAC policies
- Pod security policies
- Image scanning in CI/CD
- Automated backups via CronJobs
- Disaster recovery procedures

## Deployment Workflow

### Initial Setup

1. **Create namespace:**
   ```bash
   kubectl create namespace raas
   ```

2. **Deploy base + overlay:**
   ```bash
   # Local development
   kubectl apply -k infrastructure/k8s/overlays/local/

   # OR Production
   kubectl apply -k infrastructure/k8s/overlays/production/
   ```

3. **Verify deployment:**
   ```bash
   kubectl get pods -n raas
   kubectl get svc -n raas
   kubectl get ingress -n raas
   kubectl get pvc -n raas
   ```

4. **Check logs:**
   ```bash
   kubectl logs -f deployment/api -n raas
   kubectl logs -f deployment/embedder -n raas
   ```

5. **Test services:**
   ```bash
   # Port-forward for local testing
   kubectl port-forward svc/api 8000:8000 -n raas
   kubectl port-forward svc/frontend 3000:3000 -n raas

   # Test API
   curl http://localhost:8000/api/v1/health
   ```

### Updates

```bash
# Update image version
kubectl set image deployment/api api=raas-api:v2 -n raas

# Monitor rollout
kubectl rollout status deployment/api -n raas

# Rollback if needed
kubectl rollout undo deployment/api -n raas
```

### Cleanup

```bash
# Delete all resources
kubectl delete -k infrastructure/k8s/overlays/local/

# Or delete namespace (removes everything)
kubectl delete namespace raas
```

## Resource Estimates

### Local Development

| Service | CPU Request | Memory Request | Storage |
|---------|-------------|----------------|---------|
| PostgreSQL | 200m | 512Mi | 2Gi |
| Qdrant | 500m | 1Gi | 5Gi |
| API | 200m | 512Mi | 2Gi |
| Embedder | 500m | 1Gi | 5Gi |
| Generator | 500m | 1Gi | - |
| Ollama | 1000m | 2Gi | 10Gi |
| Frontend | 100m | 256Mi | - |
| **Total** | **3000m (3 CPU)** | **6.25Gi** | **24Gi** |

**Minimum local machine:** 4 CPU cores, 8Gi RAM, 30Gi disk

### Production

| Service | CPU Request | Memory Request | Replicas | Total CPU | Total Memory |
|---------|-------------|----------------|----------|-----------|--------------|
| PostgreSQL | 500m | 1Gi | 1 | 500m | 1Gi |
| Qdrant | 1000m | 2Gi | 1 | 1000m | 2Gi |
| API | 500m | 1Gi | 2 | 1000m | 2Gi |
| Embedder | 1000m | 2Gi | 2 | 2000m | 4Gi |
| Generator | 500m | 1Gi | 2 | 1000m | 2Gi |
| Ollama | 1000m | 2Gi | 1 | 1000m | 2Gi |
| Frontend | 100m | 256Mi | 2 | 200m | 512Mi |
| **Total** | | | | **6700m (6.7 CPU)** | **13.5Gi** |

**Production cluster:** 3 nodes × 4 CPU × 8Gi RAM = 12 CPU, 24Gi RAM

## Testing Strategy

### Pre-deployment

1. Validate YAML syntax:
   ```bash
   kubectl apply --dry-run=client -k infrastructure/k8s/overlays/local/
   ```

2. Check Kustomize build:
   ```bash
   kubectl kustomize infrastructure/k8s/overlays/local/ > rendered.yaml
   cat rendered.yaml  # Review rendered manifests
   ```

### Post-deployment

1. **Health checks:**
   ```bash
   kubectl get pods -n raas
   kubectl describe pod <pod-name> -n raas
   kubectl logs <pod-name> -n raas
   ```

2. **Service connectivity:**
   ```bash
   kubectl exec -it deployment/api -n raas -- curl http://qdrant:6333/
   kubectl exec -it deployment/api -n raas -- curl http://embedder:8001/health
   ```

3. **Scaling test:**
   ```bash
   # Trigger HPA
   kubectl run -it --rm load-generator --image=busybox -n raas -- /bin/sh
   # Generate load on API

   # Watch HPA scale
   kubectl get hpa -n raas -w
   ```

4. **Rollout test:**
   ```bash
   kubectl set image deployment/api api=raas-api:v2 -n raas
   kubectl rollout status deployment/api -n raas
   kubectl rollout undo deployment/api -n raas
   ```

## Documentation Structure

Each service directory will include:
- `README.md` - Service description and configuration notes
- YAML manifests with inline comments
- Example kubectl commands

Base `infrastructure/k8s/README.md` will include:
- Deployment instructions
- Troubleshooting guide
- Common operations reference

## Security Considerations

### Immediate

- Secrets for sensitive data (passwords, tokens)
- Non-root container users where possible
- Resource limits to prevent DoS
- Network isolation via ClusterIP (no external exposure except Ingress)

### Future

- NetworkPolicies for pod-to-pod restrictions
- RBAC for least-privilege access
- Pod Security Standards/Policies
- Image vulnerability scanning
- Encrypted secrets (sealed-secrets, external secret managers)

## Monitoring & Observability

### Built-in

- Health probes (liveness/readiness)
- kubectl logs for log aggregation
- kubectl top for resource usage
- Events via kubectl describe

### Future

- Prometheus metrics collection
- Grafana dashboards
- Distributed tracing (Jaeger)
- Log aggregation (ELK stack)
- Alerting (Prometheus Alertmanager)

## Conclusion

This Kubernetes scaffolding design provides:

✅ **Modularity:** Service-per-directory structure
✅ **Flexibility:** Kustomize overlays for local/production
✅ **Scalability:** HPA, multiple replicas, load balancing
✅ **Reliability:** StatefulSets, health probes, rollout strategies
✅ **Type I Compliance:** Meets all INFS3208 requirements
✅ **Production-Ready:** Best practices, proper resource management
✅ **Future-Proof:** Easy to extend with monitoring, security, advanced features

The scaffolding can be created now and updated as services evolve before actual deployment.

## Next Steps

1. **Create manifest files** (implementation phase)
2. **Test locally** with Kind/Minikube
3. **Iterate** as docker-compose services stabilize
4. **Deploy to production** when ready
5. **Add monitoring** and advanced features
