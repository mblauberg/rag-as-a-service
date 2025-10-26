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

RAAS (Retrieval-Augmented Generation as a Service) is an intelligent document search platform using semantic understanding and AI. Unlike traditional keyword search that matches exact words, RAAS uses vector embeddings to understand document meaning, enabling users to find information based on concepts rather than exact text matches.

The platform implements Retrieval-Augmented Generation (RAG), combining vector similarity search with LLMs for AI-generated summaries with citations. It uses sentence-transformers to convert documents into 384-dimensional vectors, enabling fast semantic searches through HNSW indexing.

### Motivation

Organisations accumulate massive repositories of technical specs, legal contracts, research papers, and internal wikis. Traditional Boolean keyword search can't capture semantic nuances, forcing users to craft specific queries and manually sift through results.

For example, a legal firm searching "contract breach" would miss cases described as "agreement violation" or "contractual default." RAAS solves this by understanding semantic relationships, surfacing relevant cases regardless of terminology. This reduces time spent hunting for information, improves decision-making, and enables easier knowledge access.

### Objectives and Features

**Primary Objective:** Build a scalable, intelligent document search system that understands semantic meaning and provides AI-powered summaries.

**Core Features:**
1. **Multi-format Document Upload** - TXT, PDF, DOCX, CSV, Markdown with drag-and-drop interface
2. **Semantic Search** - Vector similarity search using 384-dimensional embeddings
3. **AI-Powered Summarisation** - LLM-generated summaries with inline citations
4. **Document Management** - Full CRUD operations for document lifecycle
5. **Multi-Provider LLM Support** - OpenAI GPT, Anthropic Claude, Google Gemini for production reliability
6. **Real-time Status Tracking** - Asynchronous processing with upload/embedding monitoring
7. **Responsive Web Interface** - Mobile-friendly React/Tailwind CSS UI

### Limitations of Traditional Computing

Traditional monolithic deployments face critical constraints:

**Scalability Issues:** Embedding generation is computationally expensive. Monolithic apps can't scale components independently, forcing you to scale the entire application during traffic spikes. Vertical scaling hits physical limits and becomes expensive.

**Resource Inefficiency:** Fixed provisioning leads to over-provisioning (wasting resources) or under-provisioning (causing performance issues). Embedding models consume 2GB+ memory, which concurrent requests can quickly exhaust.

**Reliability Problems:** Single-server deployments create single points of failure. Hardware failures or crashes cause complete downtime. Manual failover is slow and error-prone.

**Operational Complexity:** Updates require system restarts, causing interruptions. Rollbacks are manual. Dependency conflicts complicate maintenance.

### Cloud Computing Benefits

Cloud-native architecture solves these through microservices, containerisation, and orchestration:

**Elastic Scalability:** Kubernetes HPA automatically scales services based on CPU/memory usage. API service scales from 2 to 5 replicas during traffic spikes while embedder stays at 1 replica during off-peak hours, optimising resource use and costs.

**High Availability:** Multiple replicas across nodes ensure fault tolerance. If one pod crashes, Kubernetes automatically restarts it while remaining pods handle traffic. Load balancing prevents hotspots.

**Zero-Downtime Deployments:** Rolling updates deploy new versions incrementally while maintaining availability. Failed deployments automatically rollback within seconds.

**Cost Optimisation:** HPA scales down during low traffic. Preemptible VMs offer 60-80% discounts. Pay-per-use eliminates over-provisioning waste.

**Infrastructure as Code:** Kubernetes manifests ensure consistency from development to production. Version-controlled infrastructure enables audit trails and rapid disaster recovery.

---

## 2. TECHNICAL SOLUTIONS

### Cloud Technologies

**Frontend Technologies:**
- **React 18 + TypeScript** - Component-based UI with type safety
- **Tailwind CSS + shadcn/ui** - Utility-first styling
- **React Query** - Server state management with caching

**Backend Services:**
- **FastAPI (Python 3.11)** - Async web framework with OpenAPI documentation
- **PostgreSQL 15** - Relational database for metadata and text chunks
- **Qdrant** - Vector database with HNSW indexing
- **sentence-transformers** - Embedding model (`all-MiniLM-L6-v2`) for 384-dim vectors
- **Cloud LLM Providers** - OpenAI (GPT-5, GPT-5 Mini), Anthropic (Claude), Google (Gemini)
- **SQLAlchemy + asyncpg** - Async ORM with non-blocking driver

**Cloud Infrastructure:**
- **Docker** - Containerisation of 7 microservices
- **Google Kubernetes Engine (GKE)** - Managed Kubernetes orchestration
- **NGINX Ingress Controller** - Layer 7 load balancing
- **Horizontal Pod Autoscaler (HPA)** - Auto-scaling on CPU (70%) and memory (80%)
- **Persistent Volumes** - Durable storage for PostgreSQL and Qdrant

**Architecture Patterns:**
- Microservice architecture (7 independent services)
- Database-per-service (PostgreSQL for relational, Qdrant for vectors)
- API Gateway pattern (centralised entry point)
- Event-driven async processing (non-blocking I/O)
- Health check patterns (liveness/readiness probes)

### Monthly Cost Estimation

**Deployment Options:** GCP (production) or Kind (local demo, recommended for marking session)

**GCP Production Deployment (us-central1, 730 hours/month)**

| **Resource** | **Specification** | **Unit Cost** | **Quantity** | **Monthly Cost** |
|--------------|-------------------|---------------|--------------|------------------|
| **GKE Cluster Management** | Zonal cluster | $72.00/month | 1 cluster | $72.00 |
| **Compute Nodes** | e2-standard-4 (4 vCPU, 16GB) | $97.83/node/month | 3 nodes | $293.49 |
| **Persistent Disk SSD** | PostgreSQL data (in-cluster) | $0.17/GB/month | 10 GB | $1.70 |
| **Persistent Disk SSD** | Qdrant vectors (in-cluster) | $0.17/GB/month | 20 GB | $3.40 |
| **Persistent Disk SSD** | Model cache (embedder) | $0.17/GB/month | 5 GB | $0.85 |
| **Disk Snapshots** | Daily backups (7-day retention) | $0.026/GB/month | 50 GB | $1.30 |
| **Load Balancer** | TCP forwarding rule (Layer 4) | $0.025/hour | 730 hours | $18.25 |
| **Egress Traffic** | Within us regions | $0.01/GB | 50 GB | $0.50 |
| **Container Registry** | Docker image storage | $0.026/GB/month | 15 GB | $0.39 |
| **Cloud Logging** | Structured logs (5GB limit) | $0.50/GB/month | 5 GB | $2.50 |
| **TOTAL** | | | | **$394.38** |

**Cost Optimisations:** 1-year commitment reduces compute by 25% (~$73 savings → **$320/month**). HPA dynamic scaling saves ~30% off-peak. Preemptible VMs reduce dev/staging costs by 70%.

**Local Demo (Recommended for Marking):** Kind cluster on local machine. $0 cost. No network dependencies. Guaranteed availability. Requires Docker Desktop, 16GB RAM, 50GB disk.

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
