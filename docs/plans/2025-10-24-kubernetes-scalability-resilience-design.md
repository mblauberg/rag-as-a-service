# Kubernetes Scalability, Reliability, and Resilience Design

**Date:** 2025-10-24
**Author:** RAAS Development Team
**Status:** Approved

## Executive Summary

This design document outlines the comprehensive Kubernetes implementation for the RAAS (Retrieval-Augmented Generation as a Service) platform. The implementation focuses on scalability, reliability, and resilience using Kubernetes orchestration with a hybrid local/cloud deployment strategy.

**Key Features:**
- Hybrid deployment: Local development (Kind) and cloud production (GCP)
- Kustomize-based configuration management with environment-specific overlays
- Horizontal Pod Autoscaling (HPA) for stateless services
- Multi-replica deployments with anti-affinity for high availability
- Comprehensive health checks and auto-recovery mechanisms
- Zero-downtime rolling updates with rollback capability
- StatefulSets for databases (local) and managed services (cloud)

**Alignment with Marking Criteria:**
This design directly addresses the INFS3208 Type I project requirements:
- Microservice architecture and containerization (2 marks)
- Scalability with dynamic container adjustment (1 mark)
- Reliability with node/container failure resilience (1 mark)
- Load balancing (1 mark)
- Kubernetes orchestration (3 marks)
- Rollout and rollback (1 mark)
- Implementation originality and completeness (3 marks)

## 1. Architecture Overview

### 1.1 Deployment Strategy

The RAAS platform uses a **Kustomize-based configuration strategy** with base manifests containing common configurations and environment-specific overlays for local (Kind) and cloud (GCP) deployments.

**Architecture Diagram:**
```
┌─────────────────────────────────────────────────────────────┐
│                     NGINX Ingress Controller                 │
│              (Path-based routing: / → Frontend)              │
│                    (/api/* → API Service)                    │
└────────────────────┬───────────────────────────┬─────────────┘
                     │                           │
        ┌────────────▼──────────┐   ┌───────────▼──────────┐
        │   Frontend Service    │   │    API Service       │
        │  (2-5 replicas, HPA)  │   │  (2-10 replicas, HPA)│
        └───────────────────────┘   └──────────┬───────────┘
                                               │
                                    ┌──────────▼──────────┐
                                    │  Embedder Service   │
                                    │ (2-8 replicas, HPA) │
                                    └──────────┬──────────┘
                                               │
                         ┌─────────────────────┼──────────────────┐
                         │                     │                  │
                    ┌────▼──────┐      ┌──────▼──────┐   ┌──────▼──────┐
                    │ PostgreSQL│      │   Qdrant    │   │   Uploads   │
                    │StatefulSet│      │ StatefulSet │   │     PVC     │
                    └───────────┘      └─────────────┘   └─────────────┘
```

### 1.2 Local Environment (Kind)

**Purpose:** Complete local development environment

**Components:**
- Single-node Kind cluster with NGINX Ingress
- All services run in-cluster including PostgreSQL and Qdrant as StatefulSets
- PersistentVolumeClaims backed by local-path storage
- Port mappings: 80 (HTTP), 443 (HTTPS)

**Benefits:**
- No cloud costs during development
- Complete offline capability
- Fast iteration cycles
- Identical API surface to production

### 1.3 Cloud Environment (GCP/GKE)

**Purpose:** Production-ready deployment with managed services

**Components:**
- Multi-node GKE cluster with Cluster Autoscaler
- Application services (API, Embedder, Frontend) as Deployments
- Cloud SQL for PostgreSQL (managed service)
- Qdrant as StatefulSet with GCP persistent disks
- NGINX Ingress with external load balancer
- Multi-zone deployment for high availability

**Benefits:**
- Managed database with automated backups
- Cloud-native scaling and reliability
- Professional production architecture
- Reduced operational burden

### 1.4 Kustomize Structure

```
infrastructure/k8s/
├── base/                           # Common manifests
│   ├── namespace.yaml              # raas namespace
│   ├── api/
│   │   ├── deployment.yaml         # API Deployment
│   │   ├── service.yaml            # ClusterIP Service
│   │   ├── hpa.yaml                # HorizontalPodAutoscaler
│   │   └── pdb.yaml                # PodDisruptionBudget
│   ├── embedder/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── hpa.yaml
│   │   └── pdb.yaml
│   ├── frontend/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── hpa.yaml
│   │   └── pdb.yaml
│   ├── postgres/
│   │   ├── statefulset.yaml        # PostgreSQL StatefulSet
│   │   ├── service.yaml            # Headless service
│   │   ├── pvc.yaml                # PersistentVolumeClaim
│   │   └── secret.yaml             # Database credentials
│   ├── qdrant/
│   │   ├── statefulset.yaml        # Qdrant StatefulSet
│   │   ├── service.yaml
│   │   └── pvc.yaml
│   └── ingress/
│       └── ingress.yaml            # NGINX Ingress routes
├── overlays/
│   ├── local/                      # Kind-specific patches
│   │   ├── kustomization.yaml
│   │   ├── api-patch.yaml          # Reduced resources
│   │   ├── postgres-patch.yaml     # Local storage class
│   │   └── ingress-patch.yaml      # Local host routing
│   └── gcp/                        # GCP-specific patches
│       ├── kustomization.yaml
│       ├── api-patch.yaml          # Production resources
│       ├── cloudsql-proxy.yaml     # Cloud SQL proxy sidecar
│       ├── postgres-service.yaml   # Cloud SQL connection
│       └── ingress-patch.yaml      # External load balancer
```

**Kustomize Benefits:**
- DRY principle: Define once, patch for environments
- Version control friendly: Clear diffs for changes
- No templating complexity: Pure YAML with strategic merge patches
- Environment promotion: Easy to see differences between environments

## 2. Scalability Implementation

### 2.1 Horizontal Pod Autoscaling (HPA)

All stateless services implement HPA to automatically scale based on resource utilization.

**API Service:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api
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
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Pods
        value: 1
        periodSeconds: 60
```

**Scaling Configuration:**

| Service  | Min Replicas | Max Replicas | CPU Threshold | Memory Threshold | Rationale |
|----------|-------------|--------------|---------------|------------------|-----------|
| API      | 2           | 10           | 70%           | 80%              | Primary entry point, highest traffic |
| Embedder | 2           | 8            | 70%           | 80%              | Compute-intensive, ML model workload |
| Frontend | 2           | 5            | 70%           | 80%              | Static assets, less resource-intensive |

**Scaling Behavior:**
- **Scale up**: Aggressive (100% increase per minute) to handle traffic spikes
- **Scale down**: Conservative (1 pod per minute, 5-minute stabilization) to prevent flapping
- **Metrics evaluation**: Every 15 seconds with 3-minute metric history

### 2.2 Cluster Autoscaling (GCP Only)

GKE Cluster Autoscaler automatically adjusts node count based on pod scheduling needs.

**Configuration:**
- Min nodes: 2 (multi-zone: 1 per zone)
- Max nodes: 10
- Scale-up trigger: Pods in pending state due to insufficient resources
- Scale-down trigger: Node utilization < 50% for 10 minutes
- Scale-down considerations: Respects PodDisruptionBudgets

**Benefits:**
- Automatically provisions nodes when HPA scales pods
- Reduces costs by removing idle nodes
- Maintains high availability with multi-zone distribution

### 2.3 Load Balancing Strategy

**External Load Balancing:**
- NGINX Ingress Controller distributes traffic based on path routing
- Path `/` → Frontend Service
- Path `/api/*` → API Service
- Health checks at ingress level ensure traffic only to healthy pods

**Internal Load Balancing:**
- Kubernetes Service (ClusterIP) provides internal load balancing
- Round-robin distribution across pod endpoints
- Automatic endpoint updates when pods scale or fail
- Session affinity: None (stateless services)

**Service Mesh Considerations (Future):**
- Current design uses standard Kubernetes Service
- Future enhancement: Istio/Linkerd for advanced traffic management, retries, circuit breaking

### 2.4 Resource Management

Each pod specifies resource requests (guaranteed) and limits (maximum cap):

**Resource Allocation:**

| Service   | CPU Request | CPU Limit | Memory Request | Memory Limit | Rationale |
|-----------|------------|-----------|----------------|-------------|-----------|
| API       | 200m       | 500m      | 256Mi          | 512Mi       | Async I/O, moderate compute |
| Embedder  | 500m       | 1000m     | 512Mi          | 1Gi         | ML model inference, batch processing |
| Frontend  | 100m       | 200m      | 128Mi          | 256Mi       | Static file serving via NGINX |
| PostgreSQL| 500m       | 1000m     | 512Mi          | 1Gi         | Database workload |
| Qdrant    | 500m       | 1000m     | 1Gi            | 2Gi         | Vector search, memory-intensive |

**Request vs. Limit Strategy:**
- Requests: Used for scheduling decisions, guaranteed allocation
- Limits: Prevent resource exhaustion, protect cluster stability
- Ratio: ~2x limit to request allows burst capacity
- QoS Class: Burstable (requests < limits) for flexibility

**Benefits:**
- Accurate HPA decisions based on actual resource usage
- Prevents noisy neighbor problems
- Enables efficient bin packing on nodes
- Protects critical services from resource starvation

## 3. Reliability and Resilience

### 3.1 Health Checks and Auto-Recovery

Every service implements comprehensive health check mechanisms.

**Probe Types:**

1. **Liveness Probe**: Detects crashed or deadlocked containers
   - Action: Restart container if failing
   - Endpoint: `GET /api/v1/health` (or `/health`)

2. **Readiness Probe**: Detects when container isn't ready for traffic
   - Action: Remove from Service endpoints if failing
   - Endpoint: `GET /api/v1/health/ready` (or `/ready`)

3. **Startup Probe**: Gives extra time for slow-starting applications
   - Use case: Embedder service loading ML model (30-60s)
   - Action: Delays liveness/readiness checks until startup succeeds

**Configuration Example (API Service):**
```yaml
livenessProbe:
  httpGet:
    path: /api/v1/health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
  successThreshold: 1

readinessProbe:
  httpGet:
    path: /api/v1/health/ready
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
  successThreshold: 1

startupProbe:
  httpGet:
    path: /api/v1/health
    port: 8000
  initialDelaySeconds: 0
  periodSeconds: 5
  timeoutSeconds: 5
  failureThreshold: 30  # 30 * 5s = 150s max startup time
```

**Health Check Implementation:**
- API/Embedder: Check database connectivity, Qdrant reachability
- Frontend: Simple HTTP 200 response
- PostgreSQL/Qdrant: TCP socket check or HTTP endpoint

**Recovery Behavior:**
- Failed liveness → Container restart with exponential backoff
- Failed readiness → Removed from load balancer, no restart
- Restart backoff: 10s, 20s, 40s, ... up to 5 minutes

### 3.2 Multi-Replica with Pod Anti-Affinity

Services run multiple replicas distributed across nodes to survive node failures.

**Anti-Affinity Configuration:**

**Preferred Anti-Affinity (Default):**
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

**Required Anti-Affinity (GCP Critical Services):**
```yaml
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchExpressions:
        - key: app
          operator: In
          values:
          - api
      topologyKey: topology.kubernetes.io/zone
```

**Strategy:**
- **Local (Kind)**: Preferred anti-affinity (single node, best effort)
- **Cloud (GCP)**: Required zone anti-affinity for critical services (API, Embedder)
- **Topology Key**: `kubernetes.io/hostname` (node-level) or `topology.kubernetes.io/zone` (zone-level)

**Benefits:**
- Survives single node failure without service disruption
- Multi-zone deployment protects against zone outage
- Kubernetes scheduler automatically handles pod placement

### 3.3 Pod Disruption Budgets (PDB)

PDBs ensure minimum availability during voluntary disruptions (node maintenance, cluster upgrades).

**Configuration:**

**Application Services (minAvailable):**
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api
  namespace: raas
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: api
```

**Stateful Services (maxUnavailable):**
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: postgres
  namespace: raas
spec:
  maxUnavailable: 0
  selector:
    matchLabels:
      app: postgres
```

**PDB Strategy:**

| Service    | Strategy        | Value | Rationale |
|------------|----------------|-------|-----------|
| API        | minAvailable   | 1     | Always at least 1 pod serving traffic |
| Embedder   | minAvailable   | 1     | Always at least 1 pod for embeddings |
| Frontend   | minAvailable   | 1     | Always at least 1 pod serving UI |
| PostgreSQL | maxUnavailable | 0     | Never voluntarily disrupt database |
| Qdrant     | maxUnavailable | 0     | Never voluntarily disrupt vector DB |

**Behavior:**
- Prevents `kubectl drain` from removing all pods simultaneously
- GKE node upgrades respect PDBs
- Involuntary disruptions (node crash) bypass PDB
- Eviction API respects PDB limits

### 3.4 Rollout and Rollback Strategy

Deployments use **RollingUpdate** strategy for zero-downtime updates.

**RollingUpdate Configuration:**
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1         # Create 1 extra pod during update
    maxUnavailable: 0   # Never reduce available pods below desired count
```

**Rollout Process:**
1. Create new ReplicaSet with updated image
2. Scale up new ReplicaSet by 1 pod (maxSurge)
3. Wait for new pod to become ready (readiness probe)
4. Scale down old ReplicaSet by 1 pod
5. Repeat until all pods updated
6. Old ReplicaSet scaled to 0 (retained for rollback)

**Rollback Capability:**
```bash
# View rollout status
kubectl rollout status deployment/api -n raas

# View rollout history
kubectl rollout history deployment/api -n raas

# Rollback to previous version
kubectl rollout undo deployment/api -n raas

# Rollback to specific revision
kubectl rollout undo deployment/api --to-revision=2 -n raas
```

**Version Tracking:**
- All images tagged with semantic versions: `raas-api:v1`, `raas-api:v2`
- Change-cause annotation records reason for each revision
- ReplicaSet history retained (default 10 revisions)

**Testing Strategy:**
- Smoke tests run after deployment completes
- Automated rollback if smoke tests fail (via CI/CD)
- Manual rollback if issues detected post-deployment

**Benefits:**
- Zero-downtime deployments (maxUnavailable: 0)
- Instant rollback capability (switch ReplicaSet)
- Gradual rollout reduces blast radius of bugs
- Works seamlessly with PDB and HPA

## 4. Stateful Services and Storage

### 4.1 PostgreSQL Deployment Strategy

**Local Environment (Kind):**

**StatefulSet Configuration:**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: raas
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: raasdb
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        ports:
        - containerPort: 5432
          name: postgres
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
          subPath: postgres
        - name: init-scripts
          mountPath: /docker-entrypoint-initdb.d
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
      volumes:
      - name: init-scripts
        configMap:
          name: postgres-init-scripts
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: local-path
      resources:
        requests:
          storage: 10Gi
```

**Features:**
- Single replica (local development doesn't need HA)
- PersistentVolumeClaim for data persistence across pod restarts
- Init container runs migration scripts from `services/api/app/migrations/`
- Secret-based credential management
- Local-path storage class (Kind default)

**Cloud Environment (GCP):**

**Cloud SQL Strategy:**
- Replace PostgreSQL StatefulSet with Cloud SQL Proxy sidecar pattern
- Main container: Application (API service)
- Sidecar container: `cloud-sql-proxy` for secure connection

**Cloud SQL Proxy Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  template:
    spec:
      containers:
      - name: api
        image: raas-api:v1
        env:
        - name: DATABASE_URL
          value: postgresql+asyncpg://user:pass@localhost:5432/raasdb
      - name: cloud-sql-proxy
        image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:latest
        args:
        - "--structured-logs"
        - "--port=5432"
        - "project:region:instance-name"
        securityContext:
          runAsNonRoot: true
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
```

**Cloud SQL Features:**
- Managed PostgreSQL instance (automatic backups, updates)
- Private IP connection for security
- Automated backups (7-day retention, configurable)
- Point-in-time recovery
- High availability with automatic failover (if enabled)
- Cloud SQL Proxy handles authentication via IAM

**Kustomize Overlay Pattern:**
- Base: PostgreSQL StatefulSet
- Local overlay: Uses StatefulSet as-is
- GCP overlay: Removes StatefulSet, adds Cloud SQL proxy sidecar to API deployment

### 4.2 Qdrant Deployment Strategy

**Local Environment (Kind):**

**StatefulSet Configuration:**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: qdrant
  namespace: raas
spec:
  serviceName: qdrant
  replicas: 1
  selector:
    matchLabels:
      app: qdrant
  template:
    metadata:
      labels:
        app: qdrant
    spec:
      containers:
      - name: qdrant
        image: qdrant/qdrant:v1.7.4
        ports:
        - containerPort: 6333
          name: http
        - containerPort: 6334
          name: grpc
        volumeMounts:
        - name: qdrant-storage
          mountPath: /qdrant/storage
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /
            port: 6333
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /readyz
            port: 6333
          initialDelaySeconds: 5
          periodSeconds: 10
  volumeClaimTemplates:
  - metadata:
      name: qdrant-storage
    spec:
      accessModes: [ "ReadWriteOnce" ]
      storageClassName: local-path
      resources:
        requests:
          storage: 5Gi
```

**Features:**
- Single replica for local development
- Persistent storage for vector data
- HTTP (6333) and gRPC (6334) ports exposed
- Health checks for automatic recovery

**Cloud Environment (GCP):**

**StatefulSet with GCP Persistent Disks:**
```yaml
volumeClaimTemplates:
- metadata:
    name: qdrant-storage
  spec:
    accessModes: [ "ReadWriteOnce" ]
    storageClassName: ssd-rwo
    resources:
      requests:
        storage: 50Gi
```

**Configuration Changes:**
- Replicas: 1-3 (depending on requirements)
- Storage class: `ssd-rwo` (faster for vector operations)
- Larger storage: 50Gi+ for production data
- Optional: Multi-zone with separate PVCs per zone

**Future Enhancement: Qdrant Cloud**
- Replace StatefulSet with managed Qdrant Cloud instance
- Similar pattern to Cloud SQL (connection string in Secret)
- Kustomize overlay removes StatefulSet, updates connection config

**Why StatefulSet for Qdrant in GCP:**
- Cost control: Managed Qdrant Cloud is expensive
- Learning opportunity: Demonstrates StatefulSet expertise
- Flexibility: Can snapshot and restore via API
- Performance: Dedicated resources, no multi-tenancy

### 4.3 Storage Classes

**Local (Kind):**
- **Storage class**: `local-path` (Kind default)
- **Provisioner**: `rancher.io/local-path`
- **Reclaim policy**: Delete
- **Binding mode**: WaitForFirstConsumer
- **Location**: `/var/local-path-provisioner` on Kind node

**Cloud (GCP):**
- **PostgreSQL**: Not applicable (Cloud SQL)
- **Qdrant**: `ssd-rwo` (GCP SSD persistent disk)
- **Uploads**: `standard-rwo` (GCP standard persistent disk)

**Storage Class Definitions:**
```yaml
# GCP SSD for performance-critical workloads
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ssd-rwo
provisioner: kubernetes.io/gce-pd
parameters:
  type: pd-ssd
  replication-type: regional-pd  # Multi-zone replication
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true

# GCP Standard for general-purpose storage
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: standard-rwo
provisioner: kubernetes.io/gce-pd
parameters:
  type: pd-standard
  replication-type: regional-pd
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
```

**Volume Binding Mode:**
- `WaitForFirstConsumer`: Delays provisioning until pod scheduled
- Ensures volume created in same zone as pod (topology awareness)
- Prevents cross-zone mount errors

### 4.4 Data Persistence and Backup

**StatefulSet Guarantees:**
- Stable network identity: `postgres-0`, `qdrant-0`
- Ordered pod creation and termination
- Persistent volume bound to pod identity
- Volume persists across pod restarts/rescheduling

**Backup Strategy:**

**PostgreSQL (Local):**
- Manual backups: `kubectl exec` + `pg_dump`
- Automated backups: CronJob running `pg_dump` to S3/GCS
- Volume snapshots via storage provider

**PostgreSQL (Cloud SQL):**
- Automated daily backups (7-day retention)
- On-demand backups before major changes
- Point-in-time recovery (within retention window)
- Export to Cloud Storage for long-term retention

**Qdrant:**
- Snapshot API: `POST /collections/{collection}/snapshots`
- Store snapshots in GCS bucket
- CronJob for automated snapshot creation
- Restore via snapshot upload

**Disaster Recovery:**
- RTO (Recovery Time Objective): 15 minutes
- RPO (Recovery Point Objective): 24 hours (daily backups)
- Test restore procedures quarterly
- Document recovery runbooks

## 5. Deployment Workflow and Operations

### 5.1 Kubernetes Namespace and Organization

**Namespace Configuration:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: raas
  labels:
    name: raas
    environment: production
```

**Benefits:**
- Isolation: Resources scoped to namespace
- RBAC: Permissions scoped to namespace
- Resource Quotas: CPU/memory limits per namespace
- Network Policies: Traffic isolation
- Easy cleanup: `kubectl delete namespace raas`

**Resource Quotas (Optional):**
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: raas-quota
  namespace: raas
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    persistentvolumeclaims: "10"
```

### 5.2 Scripts and Automation

**`infrastructure/scripts/setup-kind.sh`**

Purpose: Create local Kind cluster with NGINX Ingress

```bash
#!/bin/bash
set -euo pipefail

CLUSTER_NAME="raas-cluster"

echo "Creating Kind cluster: $CLUSTER_NAME"
kind create cluster --name "$CLUSTER_NAME" --config - <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
EOF

echo "Installing NGINX Ingress Controller"
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

echo "Waiting for Ingress Controller to be ready"
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s

echo "Kind cluster ready!"
```

**`infrastructure/scripts/build-and-deploy.sh`**

Purpose: Build Docker images and deploy to Kubernetes

```bash
#!/bin/bash
set -euo pipefail

VERSION="${1:-latest}"
ENVIRONMENT="${2:-local}"

echo "Building images with version: $VERSION"
echo "Target environment: $ENVIRONMENT"

# Build images
docker build -t raas-api:$VERSION ./services/api
docker build -t raas-embedder:$VERSION ./services/embedder
docker build -t raas-frontend:$VERSION ./services/frontend

if [ "$ENVIRONMENT" = "local" ]; then
  # Load images into Kind cluster
  kind load docker-image raas-api:$VERSION --name raas-cluster
  kind load docker-image raas-embedder:$VERSION --name raas-cluster
  kind load docker-image raas-frontend:$VERSION --name raas-cluster
else
  # Push to container registry
  docker tag raas-api:$VERSION gcr.io/PROJECT_ID/raas-api:$VERSION
  docker tag raas-embedder:$VERSION gcr.io/PROJECT_ID/raas-embedder:$VERSION
  docker tag raas-frontend:$VERSION gcr.io/PROJECT_ID/raas-frontend:$VERSION

  docker push gcr.io/PROJECT_ID/raas-api:$VERSION
  docker push gcr.io/PROJECT_ID/raas-embedder:$VERSION
  docker push gcr.io/PROJECT_ID/raas-frontend:$VERSION
fi

# Apply Kustomize overlay
echo "Applying Kustomize overlay: $ENVIRONMENT"
kubectl apply -k infrastructure/k8s/overlays/$ENVIRONMENT/

# Wait for rollout
echo "Waiting for deployments to complete"
kubectl rollout status deployment/api -n raas --timeout=5m
kubectl rollout status deployment/embedder -n raas --timeout=5m
kubectl rollout status deployment/frontend -n raas --timeout=5m

# Wait for StatefulSets (if in local)
if [ "$ENVIRONMENT" = "local" ]; then
  kubectl rollout status statefulset/postgres -n raas --timeout=5m
  kubectl rollout status statefulset/qdrant -n raas --timeout=5m
fi

echo "Deployment complete!"

# Run smoke tests
echo "Running smoke tests"
./infrastructure/scripts/smoke-tests.sh
```

**`infrastructure/scripts/smoke-tests.sh`**

Purpose: Verify deployment health

```bash
#!/bin/bash
set -euo pipefail

API_URL="${API_URL:-http://localhost/api/v1}"

echo "Testing API health endpoint"
curl -f "$API_URL/health" || (echo "Health check failed" && exit 1)

echo "Testing API readiness endpoint"
curl -f "$API_URL/health/ready" || (echo "Readiness check failed" && exit 1)

echo "Testing frontend"
curl -f "http://localhost/" || (echo "Frontend check failed" && exit 1)

echo "All smoke tests passed!"
```

### 5.3 Deployment Commands

**Initial Setup (Local):**
```bash
# Create Kind cluster
./infrastructure/scripts/setup-kind.sh

# Build and deploy
./infrastructure/scripts/build-and-deploy.sh v1 local

# Verify deployment
kubectl get pods -n raas
kubectl get svc -n raas
kubectl get ingress -n raas

# Access application
open http://localhost
```

**Initial Setup (GCP):**
```bash
# Create GKE cluster
gcloud container clusters create raas-cluster \
  --region=us-central1 \
  --num-nodes=2 \
  --machine-type=n1-standard-2 \
  --enable-autoscaling \
  --min-nodes=2 \
  --max-nodes=10 \
  --enable-autorepair \
  --enable-autoupgrade

# Get credentials
gcloud container clusters get-credentials raas-cluster --region=us-central1

# Build and deploy
./infrastructure/scripts/build-and-deploy.sh v1 gcp

# Get external IP
kubectl get ingress -n raas
```

**Scaling Demonstrations:**
```bash
# Manual scaling
kubectl scale deployment api --replicas=5 -n raas

# Configure HPA (already in manifests)
kubectl autoscale deployment api --cpu-percent=70 --min=2 --max=10 -n raas

# View HPA status
kubectl get hpa -n raas
kubectl describe hpa api -n raas

# Load testing to trigger autoscaling
kubectl run -it --rm load-generator --image=busybox /bin/sh
# Inside pod: while true; do wget -q -O- http://api.raas.svc.cluster.local:8000/api/v1/health; done
```

**Reliability Demonstrations:**
```bash
# Delete a pod and watch it restart
kubectl delete pod -l app=api -n raas --force --grace-period=0
kubectl get pods -n raas -w

# Drain a node (if multi-node) and watch pods reschedule
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
kubectl get pods -n raas -o wide

# Uncordon node
kubectl uncordon <node-name>
```

**Rollout and Rollback Demonstrations:**
```bash
# Update to new version
kubectl set image deployment/api api=raas-api:v2 -n raas

# Watch rollout
kubectl rollout status deployment/api -n raas
kubectl get pods -n raas -w

# View rollout history
kubectl rollout history deployment/api -n raas

# Rollback to previous version
kubectl rollout undo deployment/api -n raas

# Rollback to specific revision
kubectl rollout undo deployment/api --to-revision=1 -n raas
```

### 5.4 Monitoring and Observability

**Built-in Kubernetes Tools:**
```bash
# Pod status and events
kubectl get pods -n raas
kubectl describe pod <pod-name> -n raas

# Resource usage
kubectl top pods -n raas
kubectl top nodes

# Logs
kubectl logs -f deployment/api -n raas
kubectl logs -f deployment/api -n raas --all-containers
kubectl logs -f deployment/api -n raas --previous  # Previous container (after crash)

# Events
kubectl get events -n raas --sort-by='.lastTimestamp'
```

**Kubernetes Dashboard (Optional):**
```bash
# Install dashboard
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml

# Create admin user
kubectl create serviceaccount dashboard-admin -n kube-system
kubectl create clusterrolebinding dashboard-admin \
  --clusterrole=cluster-admin \
  --serviceaccount=kube-system:dashboard-admin

# Get token
kubectl -n kube-system create token dashboard-admin

# Access dashboard
kubectl proxy
open http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/
```

**Application Metrics (Future Enhancement):**
- Prometheus for metrics collection
- Grafana for visualization
- Custom dashboards for API latency, throughput, error rates
- Alert rules for SLO violations

### 5.5 CI/CD Integration (Future Enhancement)

**GitHub Actions Workflow Example:**
```yaml
name: Deploy to Kubernetes

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Build images
      run: |
        VERSION=${{ github.sha }}
        docker build -t raas-api:$VERSION ./services/api
        docker build -t raas-embedder:$VERSION ./services/embedder
        docker build -t raas-frontend:$VERSION ./services/frontend

    - name: Push to GCR
      run: |
        echo ${{ secrets.GCP_SA_KEY }} | docker login -u _json_key --password-stdin gcr.io
        docker push gcr.io/PROJECT_ID/raas-api:$VERSION
        docker push gcr.io/PROJECT_ID/raas-embedder:$VERSION
        docker push gcr.io/PROJECT_ID/raas-frontend:$VERSION

    - name: Deploy to staging
      run: |
        kubectl apply -k infrastructure/k8s/overlays/staging/
        kubectl rollout status deployment/api -n raas-staging

    - name: Run tests
      run: ./infrastructure/scripts/smoke-tests.sh

    - name: Deploy to production (manual approval)
      if: github.ref == 'refs/heads/main'
      run: |
        kubectl apply -k infrastructure/k8s/overlays/gcp/
        kubectl rollout status deployment/api -n raas
```

## 6. Meeting Marking Criteria

### 6.1 Type I Requirements Mapping

| Requirement | Implementation | Location | Marks |
|------------|----------------|----------|-------|
| **Microservice architecture and containerization** | Three microservices (API, Embedder, Frontend) in separate containers with Dockerfiles | `services/*/Dockerfile` | 2 |
| **Scalability** | HPA adjusts replicas (2-10) based on CPU/memory without affecting running app | `base/*/hpa.yaml` | 1 |
| **Reliability** | Multi-replica with anti-affinity, health checks, PDB ensure function during failures | `base/*/deployment.yaml`, `base/*/pdb.yaml` | 1 |
| **Load balancing** | NGINX Ingress + Kubernetes Service ClusterIP | `base/ingress/ingress.yaml` | 1 |
| **Orchestration** | Complete Kubernetes setup with Deployments, StatefulSets, Services, Ingress, HPA, ConfigMaps, Secrets | `infrastructure/k8s/` | 3 |
| **Rollout and rollback** | RollingUpdate strategy with zero-downtime, `kubectl rollout undo` capability | Deployment strategy config | 1 |
| **Implementation originality** | Hybrid local/cloud with Kustomize overlays, production-grade resilience features | Complete design | 3 |

**Total: 12/12 marks** (remaining 3 marks from data size, storage, basic functionalities already implemented)

### 6.2 Demonstration Strategy

**4-Minute Presentation Breakdown:**

**Minute 1: Local Environment Showcase (60s)**
- Show Kind cluster running: `kubectl get nodes`
- Show all pods healthy: `kubectl get pods -n raas`
- Show services and ingress: `kubectl get svc,ingress -n raas`
- Access frontend in browser: `http://localhost`
- Quick upload and search to show functionality

**Minute 2: Scalability Demonstration (60s)**
- Show current HPA status: `kubectl get hpa -n raas`
- Start load test script (prepared in advance)
- Watch HPA scale pods: `kubectl get hpa -n raas -w`
- Show new pods being created: `kubectl get pods -n raas`
- Explain: "HPA automatically scaled from 2 to 5 replicas based on CPU load"

**Minute 3: Reliability Demonstration (60s)**
- Show multi-replica deployment: `kubectl get pods -n raas -o wide`
- Delete an API pod forcefully: `kubectl delete pod <api-pod> --force --grace-period=0`
- Show Kubernetes immediately creating replacement: `kubectl get pods -n raas`
- Test API during recovery - still responds (other replicas handle traffic)
- Explain: "Application remained available despite pod failure"

**Minute 4: Rollout and Architecture (60s)**
- Show rollout history: `kubectl rollout history deployment/api -n raas`
- Trigger update: `kubectl set image deployment/api api=raas-api:v2 -n raas`
- Show rolling update in progress: `kubectl rollout status deployment/api -n raas`
- Show Kustomize structure: `tree infrastructure/k8s/`
- Explain: "Zero-downtime rolling update with instant rollback capability"

**Q&A Preparation (2 minutes):**
- Why Kubernetes over Docker Swarm? → Industry standard, richer ecosystem, better for learning
- How does HPA work? → Metrics server monitors CPU/memory, controller adjusts replicas
- What happens if database pod fails? → StatefulSet recreates with same identity, volume persists
- Cost estimation? → GKE: ~$150/month, Cloud SQL: ~$50/month (minimal load)

### 6.3 Command Documentation

All demonstration commands will be documented with clear comments:

```bash
# Create local Kubernetes cluster using Kind
# Parameters: cluster name (raas-cluster), config from stdin
kind create cluster --name raas-cluster --config infrastructure/kind-config.yaml

# Apply Kustomize overlay for local environment
# Applies all base manifests with local-specific patches
kubectl apply -k infrastructure/k8s/overlays/local/

# Configure Horizontal Pod Autoscaler for API service
# Parameters: min replicas (2), max replicas (10), CPU target (70%)
kubectl autoscale deployment api --min=2 --max=10 --cpu-percent=70 -n raas

# Demonstrate zero-downtime rolling update
# Updates API container image to version v2
kubectl set image deployment/api api=raas-api:v2 -n raas

# Rollback to previous deployment version
# Reverts to last known good configuration
kubectl rollout undo deployment/api -n raas
```

## 7. Risk Assessment and Mitigation

### 7.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| StatefulSet data loss | High | Low | PersistentVolumes, automated backups, documented recovery |
| HPA thrashing | Medium | Medium | Conservative scale-down policy, stabilization windows |
| Resource exhaustion | High | Low | Resource limits, cluster autoscaling, monitoring alerts |
| Network partition | High | Low | Multi-replica with anti-affinity, health checks, timeouts |
| Image pull failures | Medium | Low | Image pull policy IfNotPresent, local registry mirror |
| Configuration drift | Medium | Medium | Kustomize for declarative config, GitOps practices |

### 7.2 Operational Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Inadequate testing | High | Medium | Comprehensive smoke tests, load testing before demo |
| Demo environment failure | High | Low | Test demo script multiple times, backup slides with screenshots |
| Time overrun | Medium | Medium | Practice presentation, strict time boundaries per section |
| Questions about unimplemented features | Medium | Medium | Honest answers, explain future enhancements, focus on what's implemented |

## 8. Future Enhancements

### 8.1 Short-term (Next Sprint)

1. **Prometheus + Grafana Monitoring**
   - Deploy Prometheus Operator for metrics collection
   - Create Grafana dashboards for API latency, throughput, error rates
   - Configure AlertManager for SLO violations

2. **GitOps with ArgoCD**
   - Deploy ArgoCD for declarative GitOps
   - Automatic sync from Git repository
   - Visual deployment pipeline

3. **Network Policies**
   - Restrict traffic between services
   - Only allow API → Embedder, API → PostgreSQL, etc.
   - Deny all by default, explicit allow rules

### 8.2 Medium-term (Future Versions)

1. **Service Mesh (Istio/Linkerd)**
   - Advanced traffic management (canary, blue-green)
   - Mutual TLS between services
   - Distributed tracing with Jaeger
   - Circuit breaking and retries

2. **Multi-Region Deployment**
   - Deploy to multiple GCP regions
   - Global load balancing with Cloud Load Balancer
   - Cross-region database replication

3. **Advanced Autoscaling**
   - Custom metrics autoscaling (requests per second, queue depth)
   - Vertical Pod Autoscaler for right-sizing
   - Cluster autoscaler with multiple node pools

### 8.3 Long-term (Production Hardening)

1. **Security Hardening**
   - Pod Security Standards (restricted)
   - RBAC with least privilege
   - Secrets management with External Secrets Operator
   - Image scanning in CI/CD pipeline

2. **Disaster Recovery**
   - Automated cross-region backups
   - Disaster recovery runbooks
   - Regular DR drills and testing
   - RTO < 5 minutes, RPO < 1 hour

3. **Cost Optimization**
   - Spot instances for non-critical workloads
   - Cluster autoscaler scale-to-zero for dev environments
   - Resource right-sizing based on actual usage
   - Reserved instances for baseline capacity

## 9. Conclusion

This Kubernetes implementation provides a comprehensive, production-ready foundation for the RAAS platform with focus on scalability, reliability, and resilience. The hybrid local/cloud approach with Kustomize overlays demonstrates advanced Kubernetes knowledge while maintaining practical development workflows.

**Key Achievements:**
- ✅ Complete Kubernetes orchestration meeting all Type I marking criteria
- ✅ Automated scaling from 2-10 replicas based on load
- ✅ High availability with multi-replica, anti-affinity, and health checks
- ✅ Zero-downtime deployments with instant rollback capability
- ✅ Professional infrastructure-as-code practices with Kustomize
- ✅ Comprehensive documentation and runbooks

**Demonstration Readiness:**
- Scripts tested and documented
- Demo sequence planned and timed
- Fallback plan (screenshots) prepared
- Q&A responses prepared

This design positions the RAAS project for maximum marks in the implementation category while providing a solid foundation for future enhancements and production deployment.

---

## Appendix A: File Structure

```
raas/
├── infrastructure/
│   ├── k8s/
│   │   ├── base/
│   │   │   ├── namespace.yaml
│   │   │   ├── api/
│   │   │   │   ├── deployment.yaml
│   │   │   │   ├── service.yaml
│   │   │   │   ├── hpa.yaml
│   │   │   │   ├── pdb.yaml
│   │   │   │   └── configmap.yaml
│   │   │   ├── embedder/
│   │   │   │   ├── deployment.yaml
│   │   │   │   ├── service.yaml
│   │   │   │   ├── hpa.yaml
│   │   │   │   └── pdb.yaml
│   │   │   ├── frontend/
│   │   │   │   ├── deployment.yaml
│   │   │   │   ├── service.yaml
│   │   │   │   ├── hpa.yaml
│   │   │   │   └── pdb.yaml
│   │   │   ├── postgres/
│   │   │   │   ├── statefulset.yaml
│   │   │   │   ├── service.yaml
│   │   │   │   ├── pvc.yaml
│   │   │   │   ├── secret.yaml
│   │   │   │   ├── configmap.yaml (init scripts)
│   │   │   │   └── pdb.yaml
│   │   │   ├── qdrant/
│   │   │   │   ├── statefulset.yaml
│   │   │   │   ├── service.yaml
│   │   │   │   ├── pvc.yaml
│   │   │   │   └── pdb.yaml
│   │   │   └── ingress/
│   │   │       └── ingress.yaml
│   │   └── overlays/
│   │       ├── local/
│   │       │   ├── kustomization.yaml
│   │       │   ├── api-patch.yaml
│   │       │   ├── embedder-patch.yaml
│   │       │   ├── frontend-patch.yaml
│   │       │   ├── postgres-patch.yaml
│   │       │   ├── qdrant-patch.yaml
│   │       │   └── ingress-patch.yaml
│   │       └── gcp/
│   │           ├── kustomization.yaml
│   │           ├── api-patch.yaml
│   │           ├── embedder-patch.yaml
│   │           ├── frontend-patch.yaml
│   │           ├── cloudsql-proxy.yaml
│   │           ├── postgres-service.yaml
│   │           ├── qdrant-patch.yaml
│   │           ├── ingress-patch.yaml
│   │           └── storageclass.yaml
│   └── scripts/
│       ├── setup-kind.sh
│       ├── build-and-deploy.sh
│       ├── smoke-tests.sh
│       └── teardown.sh
├── services/
│   ├── api/
│   │   └── Dockerfile
│   ├── embedder/
│   │   └── Dockerfile
│   └── frontend/
│       └── Dockerfile
└── docs/
    └── plans/
        └── 2025-10-24-kubernetes-scalability-resilience-design.md
```

## Appendix B: Resource Requirements

**Local Development (Kind):**
- CPU: 4 cores minimum, 8 cores recommended
- Memory: 8GB minimum, 16GB recommended
- Disk: 20GB free space
- Docker Desktop: 4GB memory, 2 CPUs allocated

**Cloud Production (GCP/GKE):**
- Node type: n1-standard-2 (2 vCPU, 7.5GB memory)
- Node count: 2-10 (autoscaling)
- Persistent disks: 50GB SSD for Qdrant
- Cloud SQL: db-f1-micro (testing) or db-n1-standard-1 (production)

**Estimated Monthly Costs (GCP):**
- GKE cluster: ~$150 (2 nodes * $0.10/hour * 730 hours)
- Cloud SQL: ~$50 (db-f1-micro)
- Persistent disks: ~$20 (50GB SSD * $0.17/GB/month + regional replication)
- Load balancer: ~$20
- **Total: ~$240/month** (minimal load, can be optimized)

## Appendix C: Glossary

- **HPA**: Horizontal Pod Autoscaler - automatically scales replicas based on metrics
- **PDB**: Pod Disruption Budget - ensures minimum availability during voluntary disruptions
- **StatefulSet**: Kubernetes workload for stateful applications with stable identities
- **Kustomize**: Configuration management tool for Kubernetes using overlays
- **Kind**: Kubernetes in Docker - local Kubernetes cluster for development
- **GKE**: Google Kubernetes Engine - managed Kubernetes service on GCP
- **RollingUpdate**: Deployment strategy that gradually replaces old pods with new ones
- **Anti-affinity**: Scheduling constraint to spread pods across nodes/zones
- **Liveness probe**: Health check that restarts unhealthy containers
- **Readiness probe**: Health check that removes unready pods from load balancer
