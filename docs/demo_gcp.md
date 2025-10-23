# Demonstration and GCP Deployment (Phases 5–6)

This document summarises the steps to prepare a demonstration of RAAS and outlines the scripts for load testing and deployment on Google Cloud Platform.  Use this when practising the demo or configuring cloud resources.

## Demonstration script

The demo should showcase the core features of RAAS within four minutes.  Before presenting, ensure that the Kind cluster is running, all pods are ready, and sample documents have been uploaded.  Prepare multiple terminal windows for different commands and open relevant browser tabs.  A suggested timeline:

1. **Introduction (0:00–0:30)** – briefly explain the problem RAAS solves and display the architecture diagram.
2. **Core functionality (0:30–1:30)** – use the frontend to upload a document, list documents, search semantically and delete a document.  Highlight success messages and UI updates.
3. **Kubernetes features (1:30–2:30)** – in a terminal, show pod status and deployments.  Point out that there are multiple API pods running behind an ingress controller.
4. **Scalability demo (2:30–3:00)** – scale the API deployment up via `kubectl scale` and watch new pods start.  Explain that Horizontal Pod Autoscaling can handle this automatically.
5. **Load balancing and load test (3:00–3:20)** – run a load testing script that uploads documents and fires search queries concurrently.  Tail API logs to show requests are balanced across pods.
6. **Rolling update and rollback (3:20–3:50)** – simulate a version upgrade using `kubectl set image` to deploy a new image.  Show that traffic continues while pods are replaced.  Optionally demonstrate a rollback via `kubectl rollout undo`.
7. **Conclusion (3:50–4:00)** – recap features, emphasise microservices architecture, autoscaling, and cost estimates.  Mention backup slides or recordings in case of demo failure.

## Load testing script

Use the following Bash script (`tests/load-test.sh`) to stress test the API and demonstrate load balancing:

```bash
#!/bin/bash

API_URL="http://localhost/api/v1"

echo "Uploading 10 concurrent documents..."
for i in {1..10}; do
  curl -X POST "$API_URL/documents/upload" \
    -F "file=@data/sample-docs/sample-$i.txt" \
    -F "title=Load Test Doc $i" &
done
wait

echo "Running 100 search queries..."
for i in {1..100}; do
  curl -X POST "$API_URL/search" \
    -H "Content-Type: application/json" \
    -d '{"query": "cloud computing architecture", "top_k": 5}' \
    -w "%{http_code}\n" -o /dev/null -s &
  if (( i % 20 == 0 )); then
    wait
  fi
done
wait

echo "Load test complete!"
```

## GCP deployment setup

Deploying RAAS to Google Cloud Platform involves creating a GKE cluster, enabling necessary APIs, and provisioning a Cloud SQL instance.  Use the script `infrastructure/scripts/setup-gcp.sh` as a starting point:

```bash
#!/bin/bash
set -e

PROJECT_ID="raas-demo-project"
REGION="australia-southeast1"
ZONE="${REGION}-a"
CLUSTER_NAME="raas-cluster"

echo "Setting up GCP project..."
gcloud config set project $PROJECT_ID

echo "Enabling required APIs..."
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable sqladmin.googleapis.com

echo "Creating GKE cluster..."
gcloud container clusters create $CLUSTER_NAME \
  --region=$REGION \
  --num-nodes=2 \
  --machine-type=e2-standard-2 \
  --enable-autoscaling \
  --min-nodes=2 \
  --max-nodes=4 \
  --enable-autorepair \
  --enable-autoupgrade \
  --disk-size=30 \
  --disk-type=pd-standard

echo "Getting cluster credentials..."
gcloud container clusters get-credentials $CLUSTER_NAME --region=$REGION

echo "Installing NGINX Ingress..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

echo "Creating Cloud SQL instance..."
gcloud sql instances create raas-postgres \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=$REGION

echo "GCP setup complete!"
```

After setting up the infrastructure, build container images, push them to a container registry (e.g. GCR) and apply the Kustomize overlays tailored for GCP (`infrastructure/k8s/overlays/gcp`).  Configure environment variables and secrets accordingly.

This document provides the context for demonstration preparation and cloud deployment.  For local development and Kubernetes details, refer to `kubernetes.md` and `docker_compose_testing.md`.