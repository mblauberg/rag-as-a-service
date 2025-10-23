# RAAS – Retrieval‑Augmented Generation as a Service

## Quick start

Detailed environment and setup instructions can be found in `docs/*`.

## Project structure
- `services/api/` – FastAPI gateway service
- `services/embedder/` – Embedding generation service
- `services/frontend/` – React web interface
- `infrastructure/k8s/` – Kubernetes manifests and Kustomize overlays
- `infrastructure/docker-compose/` – Docker Compose configurations for local development
- `docs/` – Documentation and product requirements
- `tests/` – Test suites
- `data/` – Sample documents and uploads
