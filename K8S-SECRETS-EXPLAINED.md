# Kubernetes Secrets Configuration - Explained

**Question:** Do the API keys only need to be in the secret.yaml file and not the .env files in generator and api services?

**Answer:** ✅ **YES - For Kubernetes deployment, API keys ONLY need to be in `secret.yaml` files.**

---

## How Kubernetes Configuration Works

### 🔑 API Keys Flow in Kubernetes

```
┌─────────────────────────────────────┐
│  secret.yaml (Kubernetes Secret)    │
│  - OPENAI_API_KEY                   │
│  - ANTHROPIC_API_KEY                │
│  - GOOGLE_API_KEY                   │
└──────────────┬──────────────────────┘
               │
               │ kubectl apply -f secret.yaml
               │
               ▼
┌─────────────────────────────────────┐
│  Kubernetes Secret: generator-api-keys
└──────────────┬──────────────────────┘
               │
               │ envFrom.secretRef
               │
               ▼
┌─────────────────────────────────────┐
│  Generator Pod (Container)          │
│  Environment variables injected:    │
│  - OPENAI_API_KEY=sk-proj-...       │
│  - ANTHROPIC_API_KEY=sk-ant-...     │
└─────────────────────────────────────┘
```

### 📋 Configuration Files Used in Kubernetes

#### **Generator Service**

**File:** `infrastructure/k8s/base/generator/deployment.yaml` (lines 25-29)

```yaml
envFrom:
  - configMapRef:
      name: generator-config      # ← Non-secret config
  - secretRef:
      name: generator-api-keys    # ← API KEYS FROM secret.yaml
```

**What this means:**
- ✅ API keys come from Kubernetes Secret (`secret.yaml`)
- ✅ Automatically injected as environment variables
- ❌ `.env` file in `services/generator/` is **NOT USED**

#### **API Service**

**File:** `infrastructure/k8s/base/api/deployment.yaml` (lines 31-35)

```yaml
envFrom:
  - configMapRef:
      name: api-config           # ← Service URLs, settings
  - secretRef:
      name: postgres-secret      # ← Database credentials ONLY
```

**What this means:**
- ❌ API service does NOT get API keys
- ✅ Only gets database credentials
- ✅ Calls generator service via HTTP: `http://generator:8002`
- ❌ `.env` file in `services/api/` is **NOT USED**

---

## Architecture: Why API Service Doesn't Need Keys

### Request Flow

```
User Request
    ↓
Frontend (React)
    ↓
API Service ← Does NOT have API keys
    ↓
    ├─→ Embedder Service (generates vectors)
    ├─→ Search Service (searches Qdrant)
    └─→ Generator Service ← HAS API keys, calls OpenAI/Anthropic
            ↓
        OpenAI/Anthropic API
```

**Key Point:** The API service is an orchestrator. It forwards requests to the Generator service, which actually has the API keys and makes the calls to OpenAI/Anthropic.

---

## When Are .env Files Used?

### Local Development (Running Services Directly)

**When you run:**
```bash
# Running generator service locally (not in Docker/K8s)
cd services/generator
poetry run uvicorn app.main:app --reload --port 8002
```

**Then:** `services/generator/.env` is read by the Python application

**When you run:**
```bash
# Running API service locally
cd services/api
poetry run uvicorn app.main:app --reload --port 8000
```

**Then:** `services/api/.env` is read by the Python application

### Docker/Kubernetes Deployment

**When you run:**
```bash
kubectl apply -f infrastructure/k8s/base/
```

**Then:**
- ❌ `.env` files are **IGNORED**
- ✅ ConfigMaps provide configuration
- ✅ Secrets provide API keys
- ✅ Environment variables injected into containers

---

## Summary: Where to Put API Keys

| Deployment Method | Where API Keys Go | Notes |
|-------------------|-------------------|-------|
| **Kubernetes** | `infrastructure/k8s/base/generator/secret.yaml` | ✅ Only place needed |
| **Docker Compose** | `infrastructure/docker-compose/.env` | For docker-compose deployment |
| **Local Development** | `services/generator/.env` | When running with `poetry run` |

---

## For Kubernetes Deployment: Checklist

### ✅ What You NEED

1. **API Keys in Kubernetes Secret:**
   ```yaml
   # infrastructure/k8s/base/generator/secret.yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: generator-api-keys
     namespace: raas
   type: Opaque
   stringData:
     OPENAI_API_KEY: "sk-proj-YOUR-REAL-KEY"
     ANTHROPIC_API_KEY: "sk-ant-YOUR-REAL-KEY"
     GOOGLE_API_KEY: "YOUR-GOOGLE-KEY"
   ```

2. **Apply the secret:**
   ```bash
   kubectl apply -f infrastructure/k8s/base/generator/secret.yaml
   ```

3. **Deploy the generator:**
   ```bash
   kubectl apply -f infrastructure/k8s/base/generator/deployment.yaml
   ```

### ❌ What You DON'T NEED

- ❌ `.env` file in `services/generator/` (not used in K8s)
- ❌ `.env` file in `services/api/` (not used in K8s)
- ❌ API keys in API service (it doesn't call OpenAI directly)

---

## Current File Status

### Files That Matter for Kubernetes

```bash
infrastructure/k8s/base/generator/secret.yaml     ← Real API keys HERE
infrastructure/k8s/base/postgres/secret.yaml      ← Database credentials
infrastructure/k8s/base/generator/deployment.yaml ← References secret
infrastructure/k8s/base/api/deployment.yaml       ← References postgres secret
```

### Files That DON'T Matter for Kubernetes

```bash
services/generator/.env        ← Only for local development
services/api/.env             ← Only for local development
infrastructure/docker-compose/.env ← Only for Docker Compose
```

---

## Verification

### Check if Generator Has API Keys in K8s

```bash
# Deploy the secret
kubectl apply -f infrastructure/k8s/base/generator/secret.yaml

# Check it was created
kubectl get secret generator-api-keys -n raas

# Deploy generator
kubectl apply -f infrastructure/k8s/base/generator/deployment.yaml

# Check pod has the environment variables
kubectl exec -it deployment/generator -n raas -- env | grep API_KEY

# Should show:
# OPENAI_API_KEY=sk-proj-...
# ANTHROPIC_API_KEY=sk-ant-...
```

### Check if API Service Calls Generator

```bash
# Check API service environment
kubectl exec -it deployment/api -n raas -- env | grep GENERATOR_URL

# Should show:
# GENERATOR_URL=http://generator:8002

# API service talks to generator via this URL
# Generator has the keys and calls OpenAI
```

---

## Why This Design?

### Separation of Concerns

1. **API Service:**
   - Orchestrates requests
   - Manages database
   - Coordinates between services
   - **Does NOT** need API keys

2. **Generator Service:**
   - Specialized for LLM generation
   - **Only service** that needs API keys
   - Calls OpenAI/Anthropic/Google
   - Isolated security boundary

### Security Benefits

- ✅ Only ONE service has API keys (generator)
- ✅ Easier to audit and secure
- ✅ Keys are in Kubernetes Secrets (encrypted at rest)
- ✅ Can rotate keys without touching API service

---

## Quick Answer

**For Kubernetes:**
```
API Keys → secret.yaml ONLY ✅

.env files → NOT USED ❌
```

**The .env files are red herrings for Kubernetes deployment - they're only for local development.**

---

## Need to Update Keys?

**Kubernetes:**
```bash
# 1. Edit secret.yaml with new keys
vim infrastructure/k8s/base/generator/secret.yaml

# 2. Apply the update
kubectl apply -f infrastructure/k8s/base/generator/secret.yaml

# 3. Restart generator pods to pick up new keys
kubectl rollout restart deployment/generator -n raas
```

**That's it!** API service doesn't need updating.
