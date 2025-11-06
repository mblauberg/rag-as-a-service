# Production Deployment Guide

Comprehensive guide for deploying RAaS (Retrieval-Augmented Generation as a Service) to production environments.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Docker Compose Deployment](#docker-compose-deployment)
- [Configuration Management](#configuration-management)
- [Security](#security)
- [Monitoring & Observability](#monitoring--observability)
- [Backup & Recovery](#backup--recovery)
- [Scaling](#scaling)
- [Troubleshooting](#troubleshooting)
- [Cost Optimization](#cost-optimization)

---

## Prerequisites

### Required Tools

| Tool | Minimum Version | Purpose |
|------|----------------|---------|
| Docker | 24.0+ | Container runtime |
| Kubernetes | 1.27+ | Container orchestration |
| kubectl | 1.27+ | Kubernetes CLI |
| Helm | 3.12+ | Kubernetes package manager (optional) |
| Git | 2.40+ | Source control |

### Cloud Requirements

**Minimum Resources (Small Deployment):**

| Component | CPU | Memory | Storage | Notes |
|-----------|-----|--------|---------|-------|
| API | 2 cores | 4 GB | - | Compute-optimized |
| Embedder | 2 cores | 8 GB | 10 GB | Memory-optimized, ML model cache |
| Generator | 1 core | 2 GB | - | Network-optimized |
| Search | 2 cores | 4 GB | - | Compute-optimized |
| Frontend | 1 core | 2 GB | - | Can use CDN |
| PostgreSQL | 2 cores | 8 GB | 100 GB | Storage-optimized, SSD |
| Qdrant | 2 cores | 4 GB | 50 GB | Memory-optimized, SSD |
| **Total** | **12 cores** | **32 GB** | **160 GB** | |

**Recommended for Production:**

- **CPU:** 16-24 cores (allow for autoscaling)
- **Memory:** 48-64 GB
- **Storage:** 250-500 GB SSD
- **Network:** 10 Gbps (internal), 1 Gbps (external)

### API Keys

Required for generator service:

| Provider | Required | Get API Key | Cost |
|----------|----------|-------------|------|
| **OpenAI** | Yes | https://platform.openai.com/api-keys | Pay-as-you-go |
| Anthropic | No | https://console.anthropic.com/ | Pay-as-you-go |
| Google | No | https://makersuite.google.com/app/apikey | Pay-as-you-go |

**Cost Estimates (per 1M tokens, as of 2025):**

- GPT-4o-mini: $0.15 (input) + $0.60 (output)
- GPT-4o: $2.50 (input) + $10.00 (output)
- Claude 3.5 Sonnet: $3.00 (input) + $15.00 (output)
- Gemini 1.5 Flash: $0.08 (input) + $0.30 (output)
- Gemini 1.5 Pro: $1.25 (input) + $5.00 (output)

---

## Deployment Options

### Comparison

| Option | Complexity | Cost | Scalability | Best For |
|--------|-----------|------|-------------|----------|
| **Kubernetes** | High | Medium-High | Excellent | Production, multi-region |
| **Docker Compose** | Low | Low | Limited | Development, small deployments |
| **Cloud Run** | Medium | Medium | Good | Serverless, variable traffic |
| **ECS/Fargate** | Medium | Medium-High | Very Good | AWS-native |

**Recommendation:** Kubernetes for production, Docker Compose for development/testing.

---

## Kubernetes Deployment

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Ingress (NGINX)                      │
│              SSL Termination, Routing                    │
└──────────┬───────────────────────────────┬──────────────┘
           │                               │
    ┌──────▼─────────┐           ┌────────▼─────────┐
    │   Frontend     │           │    API Gateway   │
    │  (Service)     │           │    (Service)     │
    │  NodePort      │           │    ClusterIP     │
    └────────────────┘           └────┬─────────────┘
                                      │
           ┌──────────────────────────┼──────────────┐
           │                          │              │
    ┌──────▼─────┐     ┌────────▼─────┐     ┌──────▼──────┐
    │  Embedder  │     │   Search     │     │  Generator  │
    │  (Service) │     │  (Service)   │     │  (Service)  │
    │  ClusterIP │     │  ClusterIP   │     │  ClusterIP  │
    └────────────┘     └───────┬──────┘     └─────────────┘
                               │
                    ┌──────────┼──────────┐
                    │                     │
             ┌──────▼──────┐      ┌──────▼───────┐
             │  PostgreSQL │      │    Qdrant    │
             │ (StatefulSet│      │(StatefulSet) │
             │     +PVC)   │      │     +PVC)    │
             └─────────────┘      └──────────────┘
```

### Step 1: Prepare Cluster

**Create Kubernetes Cluster:**

**AWS EKS:**

```bash
# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Create cluster
eksctl create cluster \
  --name raas-production \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.xlarge \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 10 \
  --managed
```

**Google GKE:**

```bash
gcloud container clusters create raas-production \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-4 \
  --enable-autoscaling \
  --min-nodes 2 \
  --max-nodes 10 \
  --enable-autorepair \
  --enable-autoupgrade
```

**Azure AKS:**

```bash
az aks create \
  --resource-group raas-rg \
  --name raas-production \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --enable-cluster-autoscaler \
  --min-count 2 \
  --max-count 10 \
  --generate-ssh-keys
```

### Step 2: Configure kubectl

```bash
# AWS
aws eks update-kubeconfig --region us-east-1 --name raas-production

# Google
gcloud container clusters get-credentials raas-production --zone us-central1-a

# Azure
az aks get-credentials --resource-group raas-rg --name raas-production

# Verify
kubectl cluster-info
kubectl get nodes
```

### Step 3: Create Namespaces

```bash
# Create production namespace
kubectl create namespace raas

# Create monitoring namespace (for observability)
kubectl create namespace monitoring

# Set default namespace
kubectl config set-context --current --namespace=raas
```

### Step 4: Configure Secrets

**API Keys for Generator Service:**

```bash
# Create secret from .env file
kubectl create secret generic raas-secrets \
  --from-literal=openai-api-key="sk-proj-..." \
  --from-literal=anthropic-api-key="sk-ant-..." \
  --from-literal=google-api-key="AIza..." \
  --namespace=raas

# Verify
kubectl get secrets -n raas
kubectl describe secret raas-secrets -n raas
```

**Database Credentials:**

```bash
# PostgreSQL credentials
kubectl create secret generic postgres-secret \
  --from-literal=username="raasuser" \
  --from-literal=password="$(openssl rand -base64 32)" \
  --from-literal=database="raasdb" \
  --namespace=raas

# Verify
kubectl get secret postgres-secret -o jsonpath='{.data.password}' -n raas | base64 --decode
```

### Step 5: Deploy Persistent Storage

**Storage Classes:**

```yaml
# infrastructure/k8s/base/storage-class.yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs  # or gce-pd, azure-disk
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
reclaimPolicy: Retain
volumeBindingMode: WaitForFirstConsumer
```

```bash
kubectl apply -f infrastructure/k8s/base/storage-class.yaml
```

**Persistent Volumes:**

```yaml
# PostgreSQL PVC
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data
  namespace: raas
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 100Gi
```

### Step 6: Deploy Services

**Using Kustomize (Recommended):**

```bash
# Build and preview
kubectl kustomize infrastructure/k8s/overlays/production/

# Apply production configuration
kubectl apply -k infrastructure/k8s/overlays/production/

# Monitor rollout
kubectl rollout status deployment/api -n raas
kubectl rollout status deployment/embedder -n raas
kubectl rollout status statefulset/postgres -n raas
kubectl rollout status statefulset/qdrant -n raas
```

**Verify Deployment:**

```bash
# Check pods
kubectl get pods -n raas

# Expected output:
# NAME                         READY   STATUS    RESTARTS   AGE
# api-5568799b9-abc12          1/1     Running   0          5m
# embedder-7fbd74fc9b-def34    1/1     Running   0          5m
# frontend-577c66b56d-ghi56    1/1     Running   0          5m
# generator-6567ff668d-jkl78   1/1     Running   0          5m
# postgres-0                   1/1     Running   0          5m
# qdrant-0                     1/1     Running   0          5m
# search-58d94bd7b7-mno90      1/1     Running   0          5m

# Check services
kubectl get services -n raas

# Check logs
kubectl logs -f deployment/api -n raas --tail=100
```

### Step 7: Configure Ingress

**Install NGINX Ingress Controller:**

```bash
# Using Helm
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer
```

**Configure Ingress Resource:**

```yaml
# infrastructure/k8s/base/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: raas-ingress
  namespace: raas
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - raas.example.com
    secretName: raas-tls
  rules:
  - host: raas.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000
```

**Install cert-manager (SSL Certificates):**

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Wait for pods
kubectl get pods --namespace cert-manager

# Create Let's Encrypt issuer
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### Step 8: Configure Autoscaling

**Horizontal Pod Autoscaler (HPA):**

```yaml
# infrastructure/k8s/base/api/hpa.yaml
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
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 2
        periodSeconds: 30
      selectPolicy: Max
```

**Cluster Autoscaler (Node-level):**

```bash
# AWS EKS
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

# Edit deployment to match cluster name
kubectl -n kube-system annotate deployment.apps/cluster-autoscaler \
  cluster-autoscaler.kubernetes.io/safe-to-evict="false"
```

### Step 9: Health Checks

**Kubernetes Probes:**

```yaml
# Example for API service
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  template:
    spec:
      containers:
      - name: api
        image: raas-api:latest
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /api/v1/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 3
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2000m"
            memory: "4Gi"
```

### Step 10: Monitoring Setup

**Install Prometheus + Grafana:**

```bash
# Add Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus + Grafana stack
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.retention=30d \
  --set grafana.adminPassword="$(openssl rand -base64 32)"

# Get Grafana password
kubectl get secret --namespace monitoring prometheus-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode

# Port-forward Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
```

**Access Grafana:** http://localhost:3000 (admin/password)

### Step 11: Validate Deployment

```bash
# Get external IP
kubectl get ingress -n raas

# Test API
curl https://raas.example.com/api/v1/health

# Test frontend
curl -I https://raas.example.com

# Upload test document
curl -X POST https://raas.example.com/api/v1/documents/upload \
  -F "file=@test.pdf" \
  -F "title=Test Document"

# Search
curl -X POST https://raas.example.com/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "top_k": 5}'
```

---

## Docker Compose Deployment

### For Small Production Deployments

**Use Case:** Single-server deployments, cost-sensitive, limited traffic.

### Step 1: Server Setup

**Provision Server:**

```bash
# Minimum specifications:
# - 16 GB RAM
# - 8 CPU cores
# - 200 GB SSD
# - Ubuntu 22.04 LTS

# SSH into server
ssh user@server-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin
```

### Step 2: Clone Repository

```bash
git clone https://github.com/your-org/raas.git
cd raas
```

### Step 3: Configure Environment

```bash
# Copy template
cp .env.template .env

# Edit with production values
nano .env
```

**Production .env:**

```bash
# API Keys (REQUIRED)
ENABLE_OPENAI=true
OPENAI_API_KEY=sk-proj-YOUR-REAL-KEY-HERE
DEFAULT_MODEL=openai:gpt-4o-mini

# Optional Providers
ENABLE_ANTHROPIC=false
ANTHROPIC_API_KEY=sk-ant-YOUR-KEY-HERE  # Optional

ENABLE_GOOGLE=false
GOOGLE_API_KEY=YOUR-KEY-HERE             # Optional

# Generation Settings
MAX_CHUNKS=5
TEMPERATURE=0.1
MAX_TOKENS=2000
TIMEOUT=30
```

### Step 4: Deploy

```bash
# Pull images (if using pre-built)
docker-compose -f infrastructure/docker-compose/docker-compose.yml pull

# Start services
docker-compose -f infrastructure/docker-compose/docker-compose.yml up -d

# Check status
docker-compose -f infrastructure/docker-compose/docker-compose.yml ps

# View logs
docker-compose -f infrastructure/docker-compose/docker-compose.yml logs -f --tail=100
```

### Step 5: Configure Reverse Proxy

**NGINX Configuration:**

```nginx
# /etc/nginx/sites-available/raas
upstream raas_api {
    server localhost:8000;
    keepalive 32;
}

upstream raas_frontend {
    server localhost:3000;
    keepalive 32;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name raas.example.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name raas.example.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/raas.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/raas.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # API location
    location /api/ {
        proxy_pass http://raas_api/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # File upload size
        client_max_body_size 100M;
    }

    # Frontend location
    location / {
        proxy_pass http://raas_frontend/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

**Enable Site:**

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d raas.example.com

# Enable site
sudo ln -s /etc/nginx/sites-available/raas /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 6: Automated Backups

```bash
#!/bin/bash
# /usr/local/bin/backup-raas.sh

BACKUP_DIR="/var/backups/raas"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
docker exec raas-postgres pg_dump -U raasuser raasdb | gzip > \
  $BACKUP_DIR/postgres_$DATE.sql.gz

# Backup Qdrant data
docker exec raas-qdrant tar czf - /qdrant/storage > \
  $BACKUP_DIR/qdrant_$DATE.tar.gz

# Backup environment
cp /home/user/raas/.env $BACKUP_DIR/env_$DATE

# Keep only last 7 days
find $BACKUP_DIR -type f -mtime +7 -delete

# Upload to S3 (optional)
# aws s3 sync $BACKUP_DIR s3://my-backup-bucket/raas/
```

**Crontab:**

```bash
# Run daily at 2 AM
0 2 * * * /usr/local/bin/backup-raas.sh
```

---

## Configuration Management

### Environment Variables

**Generator Service (Primary Configuration):**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENABLE_OPENAI` | Yes | `true` | Enable OpenAI provider |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `ENABLE_ANTHROPIC` | No | `false` | Enable Anthropic provider |
| `ANTHROPIC_API_KEY` | No | - | Anthropic API key |
| `ENABLE_GOOGLE` | No | `false` | Enable Google provider |
| `GOOGLE_API_KEY` | No | - | Google API key |
| `DEFAULT_MODEL` | No | `openai:gpt-4o-mini` | Default model (format: provider:model) |
| `MAX_CHUNKS` | No | `5` | Maximum chunks for generation |
| `MAX_TOKENS` | No | `2000` | Max completion tokens |
| `TEMPERATURE` | No | `0.1` | LLM temperature |
| `TIMEOUT` | No | `30` | Request timeout in seconds |

### ConfigMaps (Kubernetes)

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
  LOG_LEVEL: "INFO"
  ALLOWED_ORIGINS: "https://raas.example.com"
```

---

## Security

### Network Security

**Kubernetes Network Policies:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
  namespace: raas
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: embedder
    ports:
    - protocol: TCP
      port: 8001
  - to:
    - podSelector:
        matchLabels:
          app: search
    ports:
    - protocol: TCP
      port: 8003
  - to:
    - podSelector:
        matchLabels:
          app: generator
    ports:
    - protocol: TCP
      port: 8002
```

### API Key Rotation

```bash
#!/bin/bash
# scripts/rotate-api-keys.sh

# Generate new secret
kubectl create secret generic raas-secrets-new \
  --from-literal=openai-api-key="$NEW_OPENAI_KEY" \
  --from-literal=anthropic-api-key="$NEW_ANTHROPIC_KEY" \
  --namespace=raas

# Update deployment to use new secret
kubectl set env deployment/generator \
  --from=secret/raas-secrets-new \
  --namespace=raas

# Wait for rollout
kubectl rollout status deployment/generator -n raas

# Delete old secret
kubectl delete secret raas-secrets -n raas

# Rename new secret
kubectl patch secret raas-secrets-new \
  -p '{"metadata":{"name":"raas-secrets"}}' \
  --namespace=raas
```

### SSL/TLS Configuration

**cert-manager Certificate:**

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: raas-tls
  namespace: raas
spec:
  secretName: raas-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - raas.example.com
  - www.raas.example.com
```

---

## Monitoring & Observability

### Metrics to Monitor

**Application Metrics:**

| Metric | Type | Alert Threshold | Action |
|--------|------|----------------|--------|
| Request latency (p95) | Gauge | > 500ms | Scale up |
| Error rate | Counter | > 5% | Investigate logs |
| Search throughput | Counter | - | Capacity planning |
| Document uploads | Counter | - | Storage planning |
| LLM API failures | Counter | > 10/min | Check API keys |

**Infrastructure Metrics:**

| Metric | Type | Alert Threshold | Action |
|--------|------|----------------|--------|
| CPU utilization | Gauge | > 80% | Scale up |
| Memory utilization | Gauge | > 85% | Scale up |
| Disk usage | Gauge | > 90% | Add storage |
| Network errors | Counter | > 1% | Check network |

### Grafana Dashboards

**Import Dashboard:**

```bash
# Get Grafana API key
kubectl get secret --namespace monitoring prometheus-grafana \
  -o jsonpath="{.data.admin-password}" | base64 --decode

# Import dashboard (ID: 15759)
curl -X POST http://localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -d '{"dashboard":{"id":15759},"overwrite":true}'
```

### Logging

**Centralized Logging (ELK Stack):**

```bash
# Install Elasticsearch + Kibana
helm repo add elastic https://helm.elastic.co
helm install elasticsearch elastic/elasticsearch --namespace logging --create-namespace
helm install kibana elastic/kibana --namespace logging

# Install Filebeat
helm install filebeat elastic/filebeat --namespace logging \
  --set daemonset.enabled=true
```

### Alerting

**Prometheus AlertManager Rules:**

```yaml
# infrastructure/k8s/monitoring/alerts.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-alerts
  namespace: monitoring
data:
  alerts.yml: |
    groups:
    - name: raas_alerts
      interval: 30s
      rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }}%"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "P95 latency is {{ $value }}s"
```

---

## Backup & Recovery

### Backup Strategy

**PostgreSQL:**

```bash
# Full backup
kubectl exec -n raas postgres-0 -- \
  pg_dump -U raasuser -Fc raasdb > backup_$(date +%Y%m%d).dump

# Restore
kubectl exec -i -n raas postgres-0 -- \
  pg_restore -U raasuser -d raasdb < backup_20250131.dump
```

**Qdrant:**

```bash
# Create snapshot
kubectl exec -n raas qdrant-0 -- \
  curl -X POST http://localhost:6333/collections/documents/snapshots

# Download snapshot
kubectl cp raas/qdrant-0:/qdrant/snapshots/documents ./qdrant-backup/

# Restore
kubectl cp ./qdrant-backup/ raas/qdrant-0:/qdrant/snapshots/
kubectl exec -n raas qdrant-0 -- \
  curl -X PUT http://localhost:6333/collections/documents/snapshots/upload
```

### Disaster Recovery

**Recovery Time Objective (RTO):** 4 hours
**Recovery Point Objective (RPO):** 24 hours

**DR Runbook:**

1. **Provision new cluster** (1 hour)
2. **Restore databases** (1 hour)
3. **Redeploy services** (30 minutes)
4. **Validate functionality** (30 minutes)
5. **DNS cutover** (1 hour propagation)

---

## Scaling

### Vertical Scaling

**Increase Resources:**

```bash
kubectl set resources deployment api -n raas \
  --requests=cpu=1000m,memory=2Gi \
  --limits=cpu=4000m,memory=8Gi
```

### Horizontal Scaling

**Manual Scaling:**

```bash
# Scale deployment
kubectl scale deployment api --replicas=5 -n raas

# Scale StatefulSet
kubectl scale statefulset postgres --replicas=3 -n raas
```

**Auto-Scaling (HPA):**

Already configured in Step 8 of Kubernetes deployment.

### Database Scaling

**PostgreSQL Read Replicas:**

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-replica
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_REPLICATION_MODE
          value: "replica"
        - name: POSTGRES_MASTER_HOST
          value: "postgres-0.postgres"
```

**Qdrant Sharding:**

```yaml
# Configure sharding for >1M vectors
collections:
  documents:
    sharding:
      number_of_shards: 4
      replication_factor: 2
```

---

## Troubleshooting

### Common Issues

**1. Pod CrashLoopBackOff**

```bash
# Check logs
kubectl logs -f pod-name -n raas

# Describe pod
kubectl describe pod pod-name -n raas

# Common causes:
# - Missing secrets
# - Insufficient resources
# - Database connection failure
```

**2. Service Unavailable (503)**

```bash
# Check service endpoints
kubectl get endpoints -n raas

# Check pod readiness
kubectl get pods -n raas -o wide

# Common causes:
# - Failed health checks
# - Database down
# - Insufficient replicas
```

**3. Slow Performance**

```bash
# Check resource usage
kubectl top pods -n raas
kubectl top nodes

# Check HPA status
kubectl get hpa -n raas

# Common causes:
# - CPU/memory throttling
# - Database query performance
# - Network latency
```

### Debug Commands

```bash
# Execute command in pod
kubectl exec -it pod-name -n raas -- bash

# Copy files from pod
kubectl cp raas/pod-name:/path/to/file ./local-file

# Port forward to pod
kubectl port-forward pod-name 8000:8000 -n raas

# View events
kubectl get events -n raas --sort-by='.lastTimestamp'

# Check resource usage
kubectl describe node node-name
```

---

## Cost Optimization

### Cloud Cost Estimates

**AWS (Monthly):**

| Resource | Type | Quantity | Cost |
|----------|------|----------|------|
| EKS Cluster | - | 1 | $73 |
| EC2 Instances | t3.xlarge | 3 | $445 |
| EBS Volumes | gp3 | 500 GB | $40 |
| Load Balancer | ALB | 1 | $25 |
| Data Transfer | Outbound | 500 GB | $45 |
| **Total** | | | **~$630/month** |

**LLM API Costs (Variable):**

- 100K searches/month: ~$50
- 10K generations/month: ~$150
- **Total API costs:** ~$200/month

**Grand Total:** ~$830/month for small production deployment

### Cost Reduction Strategies

1. **Use Spot Instances:** 70% savings on compute
2. **Reserved Instances:** 40% savings for predictable workloads
3. **Efficient Model Selection:** Use gpt-4o-mini instead of gpt-4o
4. **Query Caching:** Reduce redundant LLM calls
5. **Auto-scaling:** Scale down during off-hours

---

## Checklist

### Pre-Deployment

- [ ] API keys configured
- [ ] Secrets created
- [ ] DNS configured
- [ ] SSL certificates obtained
- [ ] Backup strategy defined
- [ ] Monitoring configured
- [ ] Load testing completed

### Post-Deployment

- [ ] Health checks passing
- [ ] SSL certificate valid
- [ ] Backups running
- [ ] Monitoring dashboards configured
- [ ] Alerts configured
- [ ] Documentation updated
- [ ] Team trained on runbooks

---

## Support

- **Issues:** https://github.com/mblauberg/issues
- **Documentation:** See docs/ directory
- **Email:** mblauberg@outlook.com
