# Type I Projects — What You Need (at a glance)

Build a **scalable, reliable, microservice-based web app** with a real frontend + backend, containerise it, orchestrate it (Swarm or Kubernetes), and prove scaling, resilience, load-balancing, and rollout/rollback in your demo. Marks are awarded specifically for those capabilities.  

---

## 1) What a Type I project is

* **Goal:** A *highly scalable and available web application* using **micro-service architecture** and related cloud tech. Focus is on **deployment at scale**, **reliability**, and **resilience** (e.g., PHP/JavaScript + MySQL/NoSQL + Docker/K8s + Load Balancer). Must support **rolling updates and rollback**. 

---

## 2) Proposal requirements (apply to Type I)

Include these in ≤1000 words / 2 A4 pages:

* **Introduction:** background, motivation, objectives/features, limits of traditional computing, and **why cloud helps**.
* **Technical solutions:** which cloud tech you’ll use (frontend + backend), plus a **monthly cost estimate** for all cloud resources (VMs, K8s, networking, LBs, etc.).
* **Architecture design:** a **figure** showing workflow/framework (e.g., microservices). 
  **How it’s marked (Proposal = 5 marks):**
* Intro (2.5): background (0.5), motivation (0.5), features (0.5), limits of traditional solutions (0.5), cloud benefits (0.5).
* Technical solutions (1.5): chosen tech (1), monthly cost estimate (0.5).
* Architecture figure (1). 

---

## 3) Implementation requirements (Type I)

Your demo must show:

* **Frontend UI** that’s functional and interactive, with **≥4 distinct functionalities** (e.g., login/logout, CRUD, search, etc.).
* **Backend** (e.g., relational/non-relational DB) working with the UI.
* **Containerisation** of services (**multiple containers** in a **microservice** design).
* **Orchestration** with **Docker Swarm *or* Kubernetes** across hosts for scalability/reliability.
* **Scalability** (adjust container counts without downtime), **reliability** (keeps working despite node/container failures), **load balancing**, and **rollout/rollback**. 

---

## 4) Marking breakdown (Implementation = 15 marks, Type I)

* Frontend interactive UI — **1**
* Backend DB design/usage — **1**
* ≥4 frontend/back-end **functionalities** — **1**
* **Microservices + containers** (granular decoupling) — **2**
* **Scalability** under varying load — **1**
* **Reliability** under failures — **1**
* **Load balancing** — **1**
* **Orchestration** (Swarm or **Kubernetes**) — **3**
* **Rollout & rollback** — **1**
* **Originality/innovation/difficulty/completeness** — **3** 

---

## 5) Presentation & submission (relevant to Type I)

* **Demo week:** Present in Week 13 showing background/motivation, **architecture & tech**, **DB/storage design**, and **results & discussion**.
* **Presentation timing:** **4 minutes** + **2 minutes Q&A**. Marks can be deducted for technical demo issues (e.g., failed scaling).
* **Submission:** Proposal + source code (and data if applicable).
* **Deployment target:** Cloud (e.g., GCP) **or local** (e.g., **kind** or Docker Desktop) is acceptable. Add clear comments to each command used. 

---

## 6) Other constraints & practical notes (useful for Type I)

* You may **reuse prior code** or an open-source web project (with consent) but must **containerise** and **deploy on the cloud stack taught**.
* **Back up** code/data **weekly**.
* If using **GCP credits**, **monitor spend**, prefer **local dev/test**, then deploy. 

---

## 7) What to prioritise for full marks (Type I)

* A **clear microservice split** (auth, API, DB, gateway, worker, etc.) with separate containers.
* **Automated deploys** to a Swarm/K8s cluster with **rolling updates** and **rollback** demonstrated live.
* **Horizontal scaling** demo (replica count up/down) under a simple load test while app stays responsive.
* **Load balancer** in front of replicas; show **health checks** and **graceful failover**.
* **Reliability scenario**: kill a pod/container/node and show the app keeps serving.
* **Costed architecture** diagram that maps each component to a cloud resource + monthly estimate.
  (These map directly to the Type I rubric items above.) 