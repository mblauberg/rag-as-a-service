# Kubernetes Deployment (Phase 4)

This document summarises how to deploy RAAS on a local Kubernetes cluster using Kind and provides examples of Kubernetes manifests. Claude Code should use these guidelines when generating manifests and deployment scripts.

## Kind cluster setup

To spin up a local Kubernetes cluster, create a Kind configuration file (`infrastructure/k8s/kind-config.yaml`) similar to the following:

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: raas-cluster
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
  - role: worker
  - role: worker
```

Use a shell script (`infrastructure/scripts/setup-kind.sh`) to create the cluster, install the NGINX ingress controller, metrics server and create a namespace.  For example:

```bash
#!/bin/bash
set -e

echo "Creating kind cluster..."
kind create cluster --config infrastructure/k8s/kind-config.yaml

echo "Installing NGINX Ingress Controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

echo "Waiting for ingress controller..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s

echo "Creating namespace..."
kubectl create namespace raas

echo "Installing metrics server..."
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl patch deployment metrics-server -n kube-system --type='json' \
  -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'

echo "Cluster ready!"
kubectl cluster-info
```

## Manifest structure

Organise Kubernetes manifests into a Kustomize hierarchy:

```
infrastructure/k8s/
├── base/
│   ├── namespace.yaml
│   ├── postgres/
│   │   ├── postgres-pvc.yaml
│   │   ├── postgres-deployment.yaml
│   │   ├── postgres-service.yaml
│   │   └── postgres-secret.yaml
│   ├── qdrant/
│   │   ├── qdrant-pvc.yaml
│   │   ├── qdrant-deployment.yaml
│   │   └── qdrant-service.yaml
│   ├── api/
│   │   ├── api-deployment.yaml
│   │   ├── api-service.yaml
│   │   ├── api-hpa.yaml
│   │   └── api-configmap.yaml
│   ├── embedder/
│   │   ├── embedder-deployment.yaml
│   │   ├── embedder-service.yaml
│   │   └── embedder-hpa.yaml
│   ├── frontend/
│   │   ├── frontend-deployment.yaml
│   │   ├── frontend-service.yaml
│   │   └── frontend-configmap.yaml
│   └── ingress/
│       └── ingress.yaml
├── overlays/
│   ├── local/
│   │   └── kustomization.yaml
│   └── gcp/
│       └── kustomization.yaml
├── kind-config.yaml
└── kustomization.yaml
```

Use Horizontal Pod Autoscalers (HPA) to scale the API and embedder deployments based on CPU and memory utilisation.  Example `api-hpa.yaml`:

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
  maxReplicas: 5
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilisation
          averageUtilisation: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilisation
          averageUtilisation: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 50
          periodSeconds: 15
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
        - type: Pods
          value: 2
          periodSeconds: 15
      selectPolicy: Max
```

Expose services via an NGINX ingress resource.  A typical `ingress.yaml` routes requests to the frontend and API based on path prefixes:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: raas-ingress
  namespace: raas
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
    - http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend
                port:
                  number: 3000
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: api
                port:
                  number: 8000
```

## Build and deploy script

A helper script (`infrastructure/scripts/build-and-deploy.sh`) can build Docker images for each service, load them into the Kind cluster, apply Kustomize overlays and wait for rollouts:

```bash
#!/bin/bash
set -e

VERSION=${1:-v1}
REGISTRY=${2:-local}

echo "Building images with version: $VERSION"

docker build -t raas-api:$VERSION services/api/
kind load docker-image raas-api:$VERSION --name raas-cluster

docker build -t raas-embedder:$VERSION services/embedder/
kind load docker-image raas-embedder:$VERSION --name raas-cluster

docker build -t raas-frontend:$VERSION services/frontend/
kind load docker-image raas-frontend:$VERSION --name raas-cluster

echo "Deploying to Kubernetes..."
kubectl apply -k infrastructure/k8s/overlays/local/

kubectl rollout status deployment/api -n raas
kubectl rollout status deployment/embedder -n raas
kubectl rollout status deployment/frontend -n raas

echo "Deployment complete!"
kubectl get pods -n raas
kubectl get svc -n raas
kubectl get ingress -n raas
```

This document covers the key elements required to deploy RAAS on Kubernetes.  For GCP deployment specifics and demo preparation, see `demo_gcp.md`.