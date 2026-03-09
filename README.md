# 🏋️ Yellow Pages Sports Chatbot

A **production-grade, cloud-native AI chatbot** for finding Thai sports businesses. Built with Flask, **LangGraph** multi-agent orchestration, FAISS vector search, and GPT-4o. Deployed on **Google Kubernetes Engine (GKE)** with full **LangSmith observability**.

> 🎯 Built as a portfolio project demonstrating **AI Integration Engineer** skills: RAG, multi-agent orchestration, containerization, Kubernetes, and observability.

---

## 🚀 Live Endpoints (GKE — asia-southeast1)

| Service | URL |
|---|---|
| 💬 Frontend (React) | `http://34.87.8.226` |
| ⚙️ Backend API | `http://34.126.130.198` |
| ❤️ Health Check | `http://34.126.130.198/health` |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GKE Cluster (asia-southeast1)                 │
│                                                                  │
│  ┌──────────────────┐   nginx proxy    ┌─────────────────────┐  │
│  │  Frontend Pod ×2 │ ────/api/*────▶  │  Backend Pod ×2     │  │
│  │  React + nginx   │                  │  Flask + gunicorn   │  │
│  │  port: 80        │                  │  port: 5000         │  │
│  └──────────────────┘                  └──────────┬──────────┘  │
│         │                                         │              │
│  LoadBalancer                            ┌────────▼────────┐    │
│  34.87.8.226                             │  FAISS (3536 v) │    │
│                                          │  + GPT-4o-mini  │    │
│                                          │  + LangSmith    │    │
│                                          └─────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Multi-Agent Pipeline (per chat message)

```
User Query
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│  Chatbot Pipeline  [LangSmith traced]                    │
│                                                          │
│  1. Router Agent ──── classifies intent ──────────────┐  │
│                                                        │  │
│  2a. Business Search Agent                            │  │
│      ├─ Extract location/sport context (LLM)          │  │
│      ├─ FAISS similarity_search (k=5)                 │  │
│      └─ Generate natural Thai response (LLM)  ◀───────┤  │
│                                                        │  │
│  2b. Sports Knowledge Agent                           │  │
│      ├─ Expert advice response (LLM)          ◀───────┤  │
│      └─ Optionally calls Business Search      ◀───────┘  │
│                                                           │
│  2c. Out-of-Scope Agent (decline politely)               │
│                                                           │
│  3. Polish Agent ──── make response warm+human (LLM)     │
│                                                           │
│  4. Save to SimpleMemory (sliding window, k=3 pairs)     │
└──────────────────────────────────────────────────────────┘
    │
    ▼
Response → Frontend
```

---

## 📁 Project Structure

```
web-scraping-Chatbot-RAG/
│
├── backend/                        # Flask backend (containerized)
│   ├── app/
│   │   ├── __init__.py             # App factory + LangSmith init
│   │   ├── api/routes.py           # REST endpoints (/, /health, /chat)
│   │   ├── agents/
│   │   │   ├── graph.py            # LangGraph StateGraph — nodes, edges, conditional routing
│   │   │   ├── orchestrator.py     # Chatbot entrypoint — invokes chat_graph
│   │   │   ├── router.py           # Intent classifier @traceable
│   │   │   ├── search.py           # FAISS business search @traceable
│   │   │   ├── knowledge.py        # Sports knowledge @traceable
│   │   │   └── utils.py            # Response polish @traceable
│   │   ├── core/config.py          # App configuration
│   │   └── services/llm.py         # LLM, embeddings, vectorstore, memory
│   ├── data/
│   │   ├── raw/                    # Scraped Excel data
│   │   └── vectorstore/            # FAISS index (3,536 vectors)
│   ├── Dockerfile                  # python:3.11-slim + gunicorn
│   ├── requirements.txt
│   └── run.py                      # gunicorn entry point
│
├── frontend/                       # React frontend (containerized)
│   ├── src/                        # React + TypeScript + Shadcn/UI
│   ├── Dockerfile                  # node:18-alpine build → nginx serve
│   ├── nginx.conf                  # SPA routing + /api proxy
│   └── package.json
│
├── k8s/                            # Kubernetes manifests
│   ├── backend-deployment.yaml     # 2 replicas, CPU/mem limits, secrets
│   └── frontend-deployment.yaml    # 2 replicas, LoadBalancer port 80
│
├── scripts/
│   └── deploy-gcp.sh               # End-to-end GCP deploy script (7 steps)
│
├── scraper/                        # YellowPages web scraper
├── .env.example                    # Environment variable template
├── docker-compose.yml              # Local full-stack development
└── README.md
```

---

## 🐳 Local Development with Docker

The fastest way to run the full stack locally:

```bash
# 1. Copy and fill in environment variables
cp .env.example .env
# Edit .env with your OPENAI_API_KEY (and optionally LANGCHAIN_API_KEY)

# 2. Start both services
docker compose up

# 3. Open the app
open http://localhost:3000        # Frontend
curl http://localhost:5000/health # Backend health check
```

**Or run services individually:**

```bash
# Backend only
docker build -t yellowpages-backend ./backend
docker run --rm -p 5000:5000 -e OPENAI_API_KEY=sk-... yellowpages-backend

# Frontend only
docker build -t yellowpages-frontend ./frontend
docker run --rm -p 3000:80 yellowpages-frontend
```

---

## 🧑‍💻 Local Development (without Docker)

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

export OPENAI_API_KEY=sk-...
python run.py
# → http://localhost:5000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

---

## ☁️ GCP Deployment

### One-Command Deploy

```bash
export OPENAI_API_KEY="sk-..."
bash scripts/deploy-gcp.sh
```

The script does **7 steps automatically**:

| Step | Action |
|---|---|
| 1 | Set GCP project `earnest-cooler-377009` |
| 2 | Enable `container` + `artifactregistry` APIs |
| 3 | Create Artifact Registry repo `yellowpages-chatbot` in `asia-southeast1` |
| 4 | `docker build` + `docker push` both images |
| 5 | Create GKE Autopilot cluster `yellowpages-cluster` |
| 6 | Create Kubernetes secret with `OPENAI_API_KEY` |
| 7 | `kubectl apply` both deployment files |

### Apply Changes After Code Update

```bash
# Rebuild and push backend
docker buildx build --platform linux/amd64 \
  -t asia-southeast1-docker.pkg.dev/earnest-cooler-377009/yellowpages-chatbot/backend:latest \
  --push ./backend

# Restart the deployment to pull new image
kubectl rollout restart deployment/backend

# Watch it roll out
kubectl rollout status deployment/backend
```

---

## 🔭 LangSmith Observability

Every chat message is fully traced in the LangSmith dashboard — see each LLM call, agent decision, latency, and token cost.

### Enable Tracing

```bash
# Add your LangSmith API key to the K8s secret
kubectl patch secret app-secrets \
  -p '{"stringData":{"langsmith-api-key":"ls__your_key_here"}}'

kubectl rollout restart deployment/backend
```

Then go to **[smith.langchain.com](https://smith.langchain.com)** → project `yellowpages-chatbot`.

### What You'll See Per Chat

```
Chatbot — full pipeline
├── Router — classify query          (1 LLM call)
├── Agent — business search
│   ├── [LLM] extract context        (1 LLM call)
│   ├── [FAISS] similarity_search    (vector lookup)
│   └── [LLM] natural response       (1 LLM call)
└── Agent — polish response          (1 LLM call)
```

---

## 📋 Environment Variables

Copy `.env.example` to `.env` and fill in your values:

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ Yes | OpenAI API key for GPT-4o-mini + embeddings |
| `LANGCHAIN_TRACING_V2` | Optional | Set `true` to enable LangSmith tracing |
| `LANGCHAIN_API_KEY` | Optional | LangSmith API key (from smith.langchain.com) |
| `LANGCHAIN_PROJECT` | Optional | LangSmith project name (default: `yellowpages-chatbot`) |
| `FLASK_ENV` | Optional | `production` or `development` (default: `production`) |
| `PORT` | Optional | Backend port (default: `5000`) |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | OpenAI GPT-4o-mini |
| **Embeddings** | `text-embedding-3-small` |
| **Vector DB** | FAISS (3,536 vectors) |
| **Orchestration** | LangChain 0.3.x + custom agents |
| **Observability** | LangSmith (`@traceable` on all agents) |
| **Backend** | Flask + gunicorn |
| **Frontend** | React 18 + Vite + TypeScript + Tailwind + Shadcn/UI |
| **Containers** | Docker (multi-stage build for frontend) |
| **Orchestration** | Kubernetes (GKE Autopilot) |
| **Registry** | Google Artifact Registry |
| **Cloud** | GCP — project `earnest-cooler-377009`, region `asia-southeast1` |

---

## 🔍 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Service info + vectorstore size |
| `GET` | `/health` | Health check (used by K8s probes) |
| `POST` | `/chat` | Send a chat message |

**POST /chat**
```bash
curl -X POST http://34.126.130.198/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "หาโยคะในกรุงเทพ"}'
```
```json
{"response": "หนูพบโยคะสตูดิโอที่น่าสนใจหลายแห่งค่ะ..."}
```

---

## 🕷️ Updating Business Data

```bash
cd scraper
python yellowpages_scraper.py
# → saves to data/raw/
# Then re-run embedding script to refresh FAISS index
```

---

## 🔗 Links

- **GitHub**: [MossMojito/web-scraping-Chatbot-RAG](https://github.com/MossMojito/web-scraping-Chatbot-RAG)
- **Live Demo**: [http://34.87.8.226](http://34.87.8.226) (GKE — always on)
- **LangSmith**: [smith.langchain.com](https://smith.langchain.com) → project `yellowpages-chatbot`

---

**Built with Flask · LangChain · FAISS · GPT-4o · Docker · Kubernetes · LangSmith**
