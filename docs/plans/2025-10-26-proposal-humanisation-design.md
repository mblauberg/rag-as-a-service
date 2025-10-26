# RAAS Proposal Humanisation Design

**Date:** 2025-10-26
**Task:** Rewrite docs/PROPOSAL.md to pass AI detection whilst maintaining technical accuracy
**Approach:** Hybrid restructure (prose humanisation + keep tables for technical specs)

---

## Context

Current proposal exhibits AI writing markers:
- Perfect parallel structure in lists
- AI-typical words: "demonstrates," "achieving," "enables"
- Systematic enumeration (numbered lists everywhere)
- Predictable sentence rhythms
- Zero stylistic variation

Research on AI detection (2025) identifies:
- Higher frequency of rare academic words ("pivotal," "intricate," "showcase")
- Perfect parallelism and systematic structure
- Lower stylistic diversity and unpredictability
- Consistent coherence at cost of natural variation

---

## Requirements from prd.md

**Proposal Must Include (≤1000 words / 2 A4 pages):**

1. **Introduction** (2.5 marks):
   - Background (0.5)
   - Motivation (0.5)
   - Features (0.5)
   - Limits of traditional solutions (0.5)
   - Cloud benefits (0.5)

2. **Technical Solutions** (1.5 marks):
   - Chosen tech (1)
   - Monthly cost estimate (0.5)

3. **Architecture Design** (1 mark):
   - Figure showing workflow/framework

---

## Verified Implementation Details

From comprehensive codebase review:

### Core Technologies (Verified)
- **Frontend:** React 18, TypeScript, Tailwind CSS, shadcn/ui, Vite
- **Backend:** FastAPI (Python 3.13), PostgreSQL 15, Qdrant 1.15
- **Embeddings:** sentence-transformers/all-MiniLM-L6-v2 (384-dim)
- **LLM:** GPT-5 Mini (OpenAI, August 2025 release) + multi-provider support
- **Infrastructure:** Docker, Kubernetes, Kind (local), NGINX Ingress
- **Chunking:** Chonkie SemanticChunker (128-512 tokens, 10% overlap)

### Search Implementation (Verified)
- **Hybrid Search:** RRF fusion of vector + BM25 keyword search
- **Reranking:** cross-encoder/ms-marco-MiniLM-L-6-v2
- **Query Expansion:** Multi-query variants for coverage
- **Modes:** Vector-only, Keyword-only, Hybrid (default)

### Features Implemented (Verified)
1. Document upload (PDF, DOCX, TXT, CSV, MD) - drag-and-drop, 100MB limit
2. Semantic search - hybrid RRF + cross-encoder reranking
3. Document management - list, view, delete with cascade
4. AI summarisation - GPT-5 Mini with citations
5. Model selection - OpenAI, Ollama, Anthropic, Google
6. Real-time status - async processing tracking

### Infrastructure (Verified)
- **K8s:** 33 manifests, HPA on API (2-10), Embedder (1-3), Generator (1-2)
- **StatefulSets:** PostgreSQL (10GB PVC), Qdrant (5GB PVC)
- **Health:** Liveness/readiness probes, rolling updates
- **Scaling:** CPU 70%, Memory 80% thresholds

---

## Humanisation Strategy

### Section 1: Introduction

**Structure Changes:**
- Convert numbered "Core Functionalities" list to prose paragraph
- Embed features naturally with varied sentence structure
- Remove perfect parallel structure (not all verbs same form)
- Mix short punchy sentences with complex subordinate clauses

**Word Substitutions:**
- "demonstrates" → "shows" / "illustrates" / "uses"
- "achieving" → "through" / "via" / natural embedded phrasing
- "enables" → "allows" / "supports" / verb phrases
- Remove "pivotal," "intricate," "showcase"

**Stylistic Variation:**
- Vary sentence lengths (mix 8-word and 30-word sentences)
- Occasional passive voice for variety
- Natural transitions (not perfect "Furthermore," "Moreover" chains)
- Embed technical details in flowing prose

**Content Accuracy:**
- Background: Mention semantic understanding, vector embeddings
- Motivation: Legal/research use case with terminology mismatch
- Features: All 6 features mentioned naturally (not numbered)
- Traditional limits: Scalability, resource inefficiency, reliability, ops overhead
- Cloud benefits: Elastic scaling (HPA 2-10 replicas), HA, zero-downtime, cost optimization

### Section 2: Technical Solutions

**Structure Changes:**
- Replace 4-category lists (Frontend/Backend/Infrastructure/Patterns) with flowing paragraphs
- Embed technologies naturally in prose rather than systematic enumeration
- Keep cost table (per hybrid approach) but add contextual paragraph before it

**Content Accuracy:**
- Frontend paragraph: React 18, TypeScript, Tailwind, shadcn/ui, React Query, Vite
- Backend paragraph: FastAPI, PostgreSQL 15, Qdrant 1.15, sentence-transformers (384-dim), GPT-5 Mini, multi-provider support
- Infrastructure paragraph: Docker, K8s, Kind, NGINX Ingress, HPA (CPU 70%/Memory 80%)
- Patterns: Brief mention of microservices, database-per-service, async
- Cost table: KEEP AS TABLE with contextual intro

### Section 3: Architecture Design

**Structure Changes:**
- Keep ASCII diagram (required, functional)
- Convert service descriptions table to simplified table + prose paragraphs
- Replace arrow notation workflows with flowing prose descriptions
- Convert "Kubernetes Features" bullet list to paragraphs with embedded specs
- Keep resource allocation table with contextual sentence

**Workflows in Prose:**

**Upload:**
"Document upload starts when users drag files into the React frontend or select them via the file picker. The API gateway validates files (checking MIME types and enforcing the 100MB size limit) before storing metadata in PostgreSQL. Text extraction handles PDF, DOCX, TXT, CSV, and Markdown formats. Rather than fixed-size chunking, the system uses Chonkie's semantic chunker—this splits text based on sentence similarity rather than arbitrary token counts, producing chunks between 128-512 tokens with 10% overlap for context. The Embedder service converts these semantically-coherent chunks into 384-dimensional vectors using sentence-transformers' all-MiniLM-L6-v2 model, storing them in Qdrant's HNSW index whilst PostgreSQL maintains the point ID references for retrieval."

**Search:**
"Search queries flow through a hybrid pipeline combining three approaches. The query gets embedded into a 384-dim vector for semantic search through Qdrant, whilst simultaneously being processed by PostgreSQL's full-text search using BM25 ranking for keyword matching. Results from both sources are merged using Reciprocal Rank Fusion (RRF), then reranked with a cross-encoder model (MS MARCO MiniLM-L-6-v2) that scores query-chunk relevance. When users request summaries, the top-ranked chunks get sent to the Generator service, which uses GPT-5 Mini (or other configured models) to produce contextual answers with citations."

**Content Accuracy:**
- Architecture diagram: Keep as-is
- Service descriptions: API (2-10 HPA), Embedder (1-3), Generator (1-2), Frontend (2), PostgreSQL, Qdrant
- K8s features: Multi-replicas, health probes, rolling updates, StatefulSets, NGINX LB
- Resource allocation table: Accurate CPU/memory requests and limits

### Section 4: Conclusion

**Structure Changes:**
- Natural concluding statement without perfect enumeration
- Avoid "demonstrates," "achieving" language
- Embed key achievements in flowing sentence

**Content:**
Brief wrap-up mentioning cloud-native microservices, Kubernetes orchestration, elastic scalability (HPA), high availability (multi-replicas), operational resilience (health monitoring, zero-downtime updates).

---

## Writing Style Guidelines

**Apply Throughout:**
1. **Sentence Length Variation:** Mix short (8-12 words) with complex (25-35 words)
2. **Imperfect Parallelism:** Lists don't all start with same verb form
3. **Natural Transitions:** Avoid perfect "Furthermore," "Moreover" chains
4. **Occasional Passive Voice:** For variety, not exclusively active
5. **Subordinate Clauses:** Complex sentences with embedded details
6. **Australian English:** -ise not -ize (organise, optimise, etc.)
7. **3rd Person Academic:** Formal but not robotic
8. **Technical Precision:** All facts verified against codebase
9. **No Emojis:** Academic style
10. **Occasional Asides:** Brief qualifications or clarifications in prose

---

## Word Count Target

- **Maximum:** 1000 words (excluding diagrams/tables)
- **Current proposal:** 993 words
- **Target range:** 950-1000 words

---

## Verification Checklist

Before submission:
- [ ] All technical details verified against codebase
- [ ] GPT-5 Mini confirmed (not GPT-4o-mini)
- [ ] Semantic chunking described (not fixed-size)
- [ ] Hybrid search mentioned (not just vector)
- [ ] Australian English (-ise, whilst, etc.)
- [ ] No AI marker words (demonstrates, achieving, pivotal, intricate)
- [ ] Varied sentence lengths (8-35 words)
- [ ] Natural prose flow (not perfect enumeration)
- [ ] Tables kept for technical specs (cost, resources)
- [ ] ASCII diagram preserved
- [ ] Word count ≤1000 (excluding diagrams/tables)
- [ ] All PRD requirements covered

---

## Implementation Notes

1. Read current PROPOSAL.md fully
2. Rewrite section by section following design above
3. Verify word count as writing (stay under 1000)
4. Final pass for AI markers (search for "demonstrates," "achieving," etc.)
5. Final pass for Australian English
6. Commit with message: "docs: humanise proposal writing style whilst maintaining accuracy"
