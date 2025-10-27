# RAAS: Retrieval-Augmented Generation as a Service
## Cloud Computing Individual Project Proposal

**Student:** Michael Blauberg
**Student ID:** 45889822
**Course:** INFS3208 Cloud Computing
**Project Type:** Type I - Highly Scalable and Available Web Application
**Date:** October 2025

---

## 1. INTRODUCTION

### Background

RAAS (Retrieval-Augmented Generation as a Service) is an intelligent document search platform using semantic understanding and AI-generated summaries. The system converts documents into vector embeddings for semantic search and provides LLM-powered summaries with citations.

### Motivation

Organizations accumulate large repositories of technical documentation, research papers, and internal wikis. Traditional keyword search cannot capture semantic relationships, forcing users to craft specific queries and manually review results.

RAAS solves this by understanding semantic meaning rather than exact word matches. A search for "contract breach" will also surface documents describing "agreement violation" or "contractual default," reducing time spent searching and improving knowledge access.

### Objectives and Features

Build a scalable, intelligent document search system with the following features:

1. **Document Upload** - Multi-format support (TXT, PDF, DOCX, CSV, Markdown)
2. **Semantic Search** - Vector similarity search using 384-dimensional embeddings
3. **Hybrid Search** - Combines semantic and keyword search with rank fusion
4. **AI Summaries** - LLM-generated summaries with inline citations
5. **Document Management** - Full CRUD operations
6. **Multi-Provider LLM** - OpenAI, Anthropic, and Google integrations
7. **Real-time Status** - Asynchronous processing with progress tracking

### Limitations of Traditional Computing

**Scalability:** Monolithic applications cannot scale components independently. Embedding generation is computationally expensive, requiring entire application scaling during traffic spikes.

**Resource Inefficiency:** Fixed provisioning leads to over-provisioning waste or under-provisioning failures. Embedding models require significant memory that concurrent requests can exhaust.

**Reliability:** Single-server deployments create single points of failure. Hardware failures cause complete downtime with slow manual failover.

**Operational Complexity:** Updates require system restarts and downtime. Rollbacks are manual and error-prone.

### Cloud Computing Benefits

**Elastic Scalability:** Kubernetes Horizontal Pod Autoscaling (HPA) automatically scales services based on CPU/memory usage, enabling independent scaling of API, embedder, and search services.

**High Availability:** Multiple pod replicas across nodes ensure fault tolerance. Automatic pod restart and load balancing maintain service during failures.

**Zero-Downtime Deployments:** Rolling updates deploy incrementally while maintaining availability. Failed deployments automatically rollback.

**Cost Optimization:** HPA scales down during low traffic. Infrastructure-as-code ensures consistent deployments and rapid recovery.

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
- sentence-transformers (all-MiniLM-L6-v2) for 384-dim embeddings
- Cloud LLM APIs: OpenAI (GPT-5), Anthropic (Claude), Google (Gemini)
- SQLAlchemy with asyncpg for async database operations

**Infrastructure:**
- Docker for containerization (5 microservices + 2 databases)
- Google Kubernetes Engine (GKE) for orchestration
- NGINX Ingress Controller for load balancing
- Horizontal Pod Autoscaler (HPA) targeting 70% CPU / 80% memory
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

**Cost Optimizations:** 1-year committed use discount reduces compute by 25% (~$73 savings → $320/month). HPA dynamic scaling saves approximately 30% during off-peak hours.

**Local Demo Alternative:** Kind cluster requires Docker Desktop, 16GB RAM, 50GB disk. Zero cloud costs, no network dependencies, guaranteed availability for marking sessions.

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
  │ Frontend │   │   API    │   │  Qdrant  │
  │ (React)  │   │ Gateway  │   │ (Vector  │
  │  :3000   │   │(FastAPI) │   │   DB)    │
  │ 2 pods   │   │  :8000   │   │  :6333   │
  └──────────┘   │ 2-10 pods│   │ 1 pod    │
                 │  (HPA)   │   │ 20GB PVC │
                 └────┬─────┘   └──────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
         ▼            ▼            ▼
   ┌──────────┐ ┌──────────┐ ┌──────────┐
   │ Embedder │ │Generator │ │PostgreSQL│
   │(sentence │ │  (LLM)   │ │(Metadata)│
   │transform)│ │  :8002   │ │  :5432   │
   │  :8001   │ │ 1-2 pods │ │  1 pod   │
   │ 1-3 pods │ │  (HPA)   │ │ 10GB PVC │
   │  (HPA)   │ └────┬─────┘ └──────────┘
   └────┬─────┘      │
        │            ▼
        │      ┌──────────────┐
        │      │  Cloud LLMs  │
        └─────▶│ OpenAI/      │
               │ Anthropic/   │
               │ Google APIs  │
               └──────────────┘
```

**Service Responsibilities:**
- **Frontend:** Document upload, search, result visualisation
- **API Gateway:** Request orchestration, business logic
- **Embedder:** 384-dim vector generation (sentence-transformers)
- **Generator:** AI summaries with citations via cloud LLM providers (OpenAI/Anthropic/Google)
- **PostgreSQL:** Document metadata, text chunks, Qdrant IDs (10GB PVC)
- **Qdrant:** Vector indexing/search with HNSW (20GB PVC)

### Document Upload Workflow

```
User → Frontend → API Gateway
                      ├─► PostgreSQL (INSERT document metadata)
                      │      └─► Returns document_id
                      │
                      ├─► Chunking Service (split into ~400-token chunks with 80-token overlap)
                      │      └─► PostgreSQL (INSERT chunks with document_id)
                      │
                      └─► Embedder Service (async request)
                             ├─► sentence-transformers (generate vectors)
                             │      └─► Returns 384-dim embeddings
                             │
                             ├─► Qdrant (upsert points with metadata)
                             │      └─► Returns point_ids
                             │
                             └─► PostgreSQL (UPDATE chunks.qdrant_point_id)
                                    └─► PostgreSQL (UPDATE embedding_status='completed')
```

### Search Query Workflow

```
User Query → Frontend → API Gateway
                           ├─► Embedder (generate query embedding)
                           │      └─► Returns 384-dim vector
                           │
                           ├─► Qdrant (vector similarity search, top-k configurable 1-100, default 10)
                           │      └─► Returns [point_ids, scores]
                           │
                           ├─► PostgreSQL (JOIN chunks + documents by point_ids)
                           │      └─► Returns [chunks with metadata]
                           │
                           ├─► Generator (if model specified, uses top 5 chunks)
                           │      ├─► Format prompt with chunks
                           │      ├─► OpenAI/Anthropic/Google API (generate summary)
                           │      └─► Returns summary with citations [1][2]
                           │
                           └─► Frontend (display results + summary)
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
│  │  │  │   API    │  │ Embedder │  │Generator │         │ │ │
│  │  │  │ 2-10 pods│  │ 1-3 pods │  │ 1-2 pods │         │ │ │
│  │  │  │   HPA    │  │   HPA    │  │   HPA    │         │ │ │
│  │  │  │ 70%CPU   │  │ 70%CPU   │  │ 70%CPU   │         │ │ │
│  │  │  │ 80%Mem   │  │ 80%Mem   │  │ 80%Mem   │         │ │ │
│  │  │  └──────────┘  └──────────┘  └──────────┘         │ │ │
│  │  │                                                     │ │ │
│  │  │  ┌──────────┐                                       │ │ │
│  │  │  │ Frontend │                                       │ │ │
│  │  │  │  2 pods  │                                       │ │ │
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
- **Multi-Pod Deployments:** 2+ replicas for critical services
- **Health Probes:** Automatic pod restart and traffic routing
- **Rolling Updates:** Zero-downtime deployments
- **Rollback Support:** 10 previous revisions for instant rollback
- **Persistent Storage:** StatefulSets with PVCs ensure durability
- **Load Balancing:** NGINX distributes traffic across healthy pods
- **Self-Healing:** Automatic pod replacement

---

## 4. CONCLUSION

RAAS demonstrates cloud-native principles through microservice architecture, containerisation, and Kubernetes orchestration. The platform achieves elastic scalability via HPA, high availability via multi-replica deployments, and operational resilience via automated health monitoring and rolling updates. The architecture satisfies all INFS3208 Type I requirements: microservices, containerisation, orchestration, scalability, reliability, load balancing, and rollout/rollback.

**Week 13 Demo:** The demo will showcase (1) HPA scaling via `kubectl get hpa`, (2) rolling updates via `kubectl rollout status`, (3) instant rollback via `kubectl rollout undo`, and (4) reliability by deleting a pod and showing automatic recreation. A local Kind cluster ensures consistent performance during marking.

**Minimum Viable Demo:** Core functionality requires 4 services (Frontend, API, PostgreSQL, Qdrant) with HPA and ingress, satisfying all microservice orchestration requirements.

---

**Word Count:** 953 words
**Page Count:** 2 pages (formatted)
