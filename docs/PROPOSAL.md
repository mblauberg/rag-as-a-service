# RAAS: Retrieval-Augmented Generation as a Service
## Cloud Computing Individual Project Proposal

**Student:** Michael Blauberg
**Student ID:** 45889822
**Course:** INFS3208 Cloud Computing
**Project Type:** Type I - Highly Scalable and Available Web Application
**Date:** 23rd October 2025

---

## 1. INTRODUCTION

### Background

RAAS (Retrieval-Augmented Generation as a Service) is a document search platform that uses semantic understanding and AI-generated summaries. The system converts documents into vector embeddings for semantic search and generates LLM-powered summaries with citations.

### Motivation

Organisations accumulate large repositories of technical documentation, research papers, and internal wikis. Traditional keyword search cannot capture semantic relationships between terms. Users must craft specific queries and manually review results.

RAAS addresses this limitation by understanding semantic meaning rather than exact word matches. A search for "contract breach" will also return documents describing "agreement violation" or "contractual default". This reduces time spent searching and improves knowledge access.

### Objectives and Features

The project builds a scalable document search system with these features:

1. **Document Upload**: Multi-format support (TXT, PDF, DOCX, CSV, Markdown)
2. **Semantic Search**: Vector similarity search using 384-dimensional embeddings
3. **Hybrid Search**: Combines semantic and keyword search with rank fusion
4. **AI Summaries**: LLM-generated summaries with inline citations
5. **Document Management**: Full CRUD operations
6. **Multi-Provider LLM**: OpenAI, Anthropic, and Google integrations
7. **Real-time Status**: Asynchronous processing with progress tracking

### Limitations of Traditional Computing

**Scalability:** Monolithic applications cannot scale components independently. Embedding generation is computationally expensive and requires scaling the entire application during traffic spikes.

**Resource Inefficiency:** Fixed provisioning leads to over-provisioning waste or under-provisioning failures. Embedding models require significant memory, which concurrent requests can exhaust.

**Reliability:** Single-server deployments create single points of failure. Hardware failures cause complete downtime with slow manual failover.

**Operational Complexity:** Updates require system restarts and downtime. Rollbacks are manual and error-prone.

### Cloud Computing Benefits

**Elastic Scalability:** Kubernetes Horizontal Pod Autoscaling (HPA) automatically scales services based on CPU and memory usage. The API, embedder, and search services can scale independently.

**High Availability:** Multiple pod replicas across nodes provide fault tolerance. Automatic pod restart and load balancing maintain service during failures.

**Zero-Downtime Deployments:** Rolling updates deploy incrementally while maintaining availability. Failed deployments trigger automatic rollback.

**Cost Optimisation:** HPA scales down during low traffic periods. Infrastructure as code ensures consistent deployments and rapid recovery.

---

## 2. TECHNICAL SOLUTIONS

### Cloud Technologies

**Frontend:**
- React 18 with TypeScript for type-safe UI components
- Tailwind CSS with shadcn/ui component library
- React Query for server state management and caching

**Backend Services:**
- FastAPI (Python 3.13) for async web framework
- PostgreSQL 15 for document metadata and text chunks
- Qdrant vector database with HNSW indexing
- sentence-transformers (all-MiniLM-L6-v2) for 384-dimensional embeddings
- Cloud LLM APIs: OpenAI (GPT-5), Anthropic (Claude), Google (Gemini)
- SQLAlchemy with asyncpg for async database operations

**Infrastructure:**
- Docker for containerisation (5 microservices and 2 databases)
- Google Kubernetes Engine (GKE) for orchestration
- NGINX Ingress Controller for load balancing
- Horizontal Pod Autoscaler (HPA) targeting 70% CPU and 80% memory
- Persistent Volumes (PV) for stateful storage

### Monthly Cost Estimation

**GCP Production Deployment (us-central1, 730 hours/month):**

| Resource | Specification | Unit Cost | Quantity | Monthly Cost |
|----------|---------------|-----------|----------|--------------|
| GKE Cluster Management | Zonal cluster | $72.00/month | 1 | $72.00 |
| Compute Nodes | e2-standard-4 (4 vCPU, 16GB) | $97.83/node/month | 3 | $293.49 |
| Persistent Disk SSD | PostgreSQL + Qdrant | $0.17/GB/month | 35 GB | $5.95 |
| Disk Snapshots | Daily backups (7-day) | $0.026/GB/month | 50 GB | $1.30 |
| Load Balancer | NGINX Ingress | $0.025/hour | 730 hrs | $18.25 |
| Egress Traffic | Within US regions | $0.01/GB | 50 GB | $0.50 |
| Container Registry | Image storage | $0.026/GB/month | 15 GB | $0.39 |
| Cloud Logging | Structured logs | $0.50/GB/month | 5 GB | $2.50 |
| **TOTAL** | | | | **$394.38** |

**Cost Optimisations:** A 1-year committed use discount reduces compute costs by 25% (approximately $73 savings to $320 per month). HPA dynamic scaling saves approximately 30% during off-peak hours.

**Local Demo Alternative:** A Kind cluster requires Docker Desktop, 16GB RAM, and 50GB disk space. This approach has zero cloud costs, no network dependencies, and guaranteed availability for marking sessions.

---

## 3. ARCHITECTURE DESIGN

### Microservice Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      NGINX Ingress Controller                       │
│                (Load Balancer + Path-based Routing)                 │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
  ┌──────────┐   ┌──────────┐   ┌──────────┐
  │ Frontend │   │   API    │   │PostgreSQL│
  │ (React)  │   │ Gateway  │   │(Metadata)│
  │  :3000   │   │(FastAPI) │   │  :5432   │
  │ 2 pods   │   │  :8000   │   │  1 pod   │
  └──────────┘   │ 2-5 pods │   │ 10GB PVC │
                 │  (HPA)   │   └──────────┘
                 └────┬─────┘
                      │
         ┌────────────┼────────────┬──────────────┐
         │            │            │              │
         ▼            ▼            ▼              ▼
   ┌──────────┐ ┌──────────┐ ┌──────────┐  ┌──────────┐
   │  Search  │ │ Embedder │ │Generator │  │  Qdrant  │
   │ (Hybrid/ │ │(sentence │ │  (LLM)   │  │ (Vector  │
   │ Rerank)  │ │transform)│ │  :8002   │  │   DB)    │
   │  :8003   │ │  :8001   │ │ 1-2 pods │  │  :6333   │
   │ 1-3 pods │ │ 1-3 pods │ │  (HPA)   │  │  1 pod   │
   │  (HPA)   │ │  (HPA)   │ └────┬─────┘  │ 20GB PVC │
   └────┬─────┘ └────┬─────┘      │        └──────────┘
        │            │             ▼
        └────────────┴────────►┌──────────────┐
                               │  Cloud LLMs  │
                               │ OpenAI/      │
                               │ Anthropic/   │
                               │ Google APIs  │
                               └──────────────┘
```

**Service Responsibilities:**
- **Frontend (Port 3000):** User interface for document upload and search
- **API Gateway (Port 8000):** Request orchestration and business logic
- **Search (Port 8003):** Hybrid search (vector and keyword), reranking, fusion
- **Embedder (Port 8001):** 384-dimensional vector generation (sentence-transformers)
- **Generator (Port 8002):** AI summaries via cloud LLM providers
- **PostgreSQL:** Document metadata, text chunks, search indices (10GB)
- **Qdrant:** Vector storage and similarity search with HNSW (20GB)

### Document Upload Workflow

```
User → Frontend → API Gateway
                      ├─► PostgreSQL (store document metadata)
                      ├─► Chunking (split text into approximately 400-token chunks)
                      │      └─► PostgreSQL (store chunks)
                      └─► Embedder Service
                             ├─► Generate 384-dimensional vectors
                             ├─► Qdrant (store vectors)
                             └─► PostgreSQL (update status='completed')
```

### Search Query Workflow

```
User → Frontend → API Gateway → Search Service
                                      ├─► Embedder (query vector)
                                      ├─► Qdrant (vector search)
                                      ├─► PostgreSQL (keyword search)
                                      ├─► Fusion (combine results)
                                      ├─► Reranking (precision scoring)
                                      └─► Return ranked chunks

                                 → Generator (if requested)
                                      ├─► Cloud LLM API
                                      └─► Summary with citations
```

### Kubernetes Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│           Google Kubernetes Engine (GKE) - us-central1          │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    raas Namespace                         │ │
│  │                                                           │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │  Deployments (Stateless Services)                   │ │ │
│  │  │                                                     │ │ │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │ │ │
│  │  │  │   API    │  │  Search  │  │ Embedder │         │ │ │
│  │  │  │ 2-5 pods │  │ 1-3 pods │  │ 1-3 pods │         │ │ │
│  │  │  │   HPA    │  │   HPA    │  │   HPA    │         │ │ │
│  │  │  │ 70%CPU   │  │ 70%CPU   │  │ 70%CPU   │         │ │ │
│  │  │  │ 80%Mem   │  │ 80%Mem   │  │ 80%Mem   │         │ │ │
│  │  │  └──────────┘  └──────────┘  └──────────┘         │ │ │
│  │  │                                                     │ │ │
│  │  │  ┌──────────┐  ┌──────────┐                        │ │ │
│  │  │  │Generator │  │ Frontend │                        │ │ │
│  │  │  │ 1-2 pods │  │  2 pods  │                        │ │ │
│  │  │  │   HPA    │  └──────────┘                        │ │ │
│  │  │  └──────────┘                                       │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  │                                                           │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │  StatefulSets (Stateful Services with PVCs)        │ │ │
│  │  │                                                     │ │ │
│  │  │  ┌──────────────────┐  ┌──────────────────┐       │ │ │
│  │  │  │   PostgreSQL     │  │     Qdrant       │       │ │ │
│  │  │  │    1 replica     │  │   1 replica      │       │ │ │
│  │  │  │ ┌──────────────┐ │  │ ┌──────────────┐ │       │ │ │
│  │  │  │ │10GB SSD PVC  │ │  │ │20GB SSD PVC  │ │       │ │ │
│  │  │  │ │(data persist)│ │  │ │(vectors)     │ │       │ │ │
│  │  │  │ └──────────────┘ │  │ └──────────────┘ │       │ │ │
│  │  │  └──────────────────┘  └──────────────────┘       │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  │                                                           │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │  NGINX Ingress Controller                          │ │ │
│  │  │  (LoadBalancer Service - External IP)              │ │ │
│  │  │  Routes: / → Frontend, /api → API Gateway          │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Observability & Management                              │ │
│  │  - Liveness Probes (restart unhealthy pods)              │ │
│  │  - Readiness Probes (route traffic only to ready pods)   │ │
│  │  - RollingUpdate Strategy (maxUnavailable:1, maxSurge:1) │ │
│  │  - Revision History: 10 (enable rollback)                │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**High Availability Features:**
- **HPA:** Automatic scaling based on metrics
- **Multi-Pod Deployments:** 2 or more replicas for critical services
- **Health Probes:** Automatic pod restart and traffic routing
- **Rolling Updates:** Zero-downtime deployments
- **Rollback Support:** 10 previous revisions for instant rollback
- **Persistent Storage:** StatefulSets with PVCs for data durability
- **Load Balancing:** NGINX distributes traffic across healthy pods
- **Self-Healing:** Automatic pod replacement

---

## 4. CONCLUSION

RAAS demonstrates cloud-native principles through microservice architecture, containerisation, and Kubernetes orchestration. The platform achieves elastic scalability through HPA, high availability through multi-replica deployments, and operational resilience through automated health monitoring and rolling updates.

The architecture satisfies all Type I requirements: microservices (5 services), containerisation (Docker), orchestration (Kubernetes and GKE), scalability (HPA), reliability (health probes and auto-restart), load balancing (NGINX Ingress), and rollout and rollback capabilities (rolling updates with 10-revision history).

**Demo Plan:** The live demonstration will show (1) HPA scaling under load, (2) rolling updates with zero downtime, (3) instant rollback on failure, and (4) self-healing through pod deletion and automatic recreation.
