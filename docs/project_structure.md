# RAAS Project Structure Overview

This document provides a high‑level overview of the directory structure for the RAAS project.  Claude Code can use this map to navigate the repository and understand where to add new files or modifications.  Each subdirectory contains its own detailed specification document.

## Top‑level directories

| Directory | Purpose |
|---|---|
| `services/` | Contains the three microservices: the FastAPI gateway (`api`), the embedding service (`embedder`) and the React frontend (`frontend`).  Each service has its own source code, configuration and Dockerfile. |
| `infrastructure/` | Holds Kubernetes manifests (under `k8s`), Docker Compose files (`docker-compose`) and helper scripts (`scripts`) for local and cloud deployments. |
| `docs/` | Documentation and project requirements.  Includes the product requirements document (PRD), this structure overview, and specifications for each component. |
| `tests/` | Test suites, both unit and integration tests.  Load test scripts also reside here. |
| `data/` | Sample documents and uploads.  `data/uploads/` is where uploaded files are stored during local development (excluded from git via `.gitignore`). |

## Service subdirectories

Within `services/`, each microservice follows a similar pattern:

| Service | Description |
|---|---|
| `services/api/` | FastAPI gateway.  Contains an `app/` package for the application code (routes, models, services, utilities), a `Dockerfile`, and Python project configuration (`pyproject.toml`).  See `api_service.md` for details. |
| `services/embedder/` | Embedding service implemented with FastAPI and sentence‑transformers.  It has an `app/` package, `tests/`, a `Dockerfile` and `pyproject.toml`.  See `embedder_service.md` for more information. |
| `services/frontend/` | React web interface built with Vite.  Contains `public/`, `src/` with components, hooks, pages and services, as well as configuration files like `package.json`, `tsconfig.json` and `Dockerfile`.  Refer to `frontend.md` for details. |

## Infrastructure

The `infrastructure/` directory contains deployment descriptors:

- `k8s/` – A base kustomization and overlays for local (Kind) and cloud (GCP) environments.  See `kubernetes.md`.
- `docker-compose/` – A development compose file to spin up all services locally.  See `docker_compose_testing.md`.
- `scripts/` – Shell scripts to automate tasks like setting up Kind, building and deploying images, or preparing GCP resources.

## Documentation and references

The `docs/` folder includes:

- `PRD.md` – The full product requirements document.
- `api_service.md`, `embedder_service.md`, `frontend.md`, `kubernetes.md`, `docker_compose_testing.md` and `demo_gcp.md` – Specifications for each part of the project.
- `REFERENCES.md` – A list of links to official documentation (FastAPI, Kubernetes, Qdrant, etc.).  Keeping references separate makes it easy to update or expand them without cluttering other files.
