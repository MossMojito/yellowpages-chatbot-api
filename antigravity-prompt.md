# 🚀 Yellow Pages Chatbot — Upgrade to Production-Grade AI System

## Context
This is a RAG-based chatbot with:
- **Frontend**: React (built via Lovable.dev)
- **Backend**: Flask API
- **AI Layer**: LangChain agents (Router, Search, Knowledge, Polish agents)
- **Vector Store**: FAISS
- **LLM**: GPT-4o
- **Currently deployed on**: Railway / Render

---

## Goal
Upgrade this project to a production-grade AI system that can run on GCP (Google Cloud Platform). This is for a job interview demonstrating AI Integration Engineer skills.

---

## Task List — Do These In Order

---

### TASK 1 — Add Dockerfile (Backend)
Create a `Dockerfile` for the Flask backend.
- Use `python:3.11-slim` as base image
- Install dependencies from `requirements.txt`
- Run with `gunicorn` on port `5000`
- Test it locally with `docker build` and `docker run`

---

### TASK 2 — Add Dockerfile (Frontend)
Create a `Dockerfile` for the React frontend.
- Use `node:18-alpine` as base image
- Build the React app
- Serve with `nginx` on port `80`

---

### TASK 3 — Add docker-compose.yml
Create a `docker-compose.yml` that runs both frontend and backend together locally for testing.
- Backend on port `5000`
- Frontend on port `3000`
- Pass environment variables (OPENAI_API_KEY, etc.)

---

### TASK 4 — Add LangSmith Observability
Add LangSmith tracing to the existing LangChain agents.
- Install `langsmith` package
- Add tracing initialization at app startup
- Wrap agent calls with tracing
- Add these env vars to `.env.example`:
  - `LANGCHAIN_TRACING_V2=true`
  - `LANGCHAIN_API_KEY=your_key`
  - `LANGCHAIN_PROJECT=yellowpages-chatbot`

---

### TASK 5 — Upgrade One Agent to LangGraph
Pick the **Router Agent** and rewrite it using LangGraph `StateGraph`.
- Define a `State` TypedDict with `messages` and `route` fields
- Create nodes for: classify → route → execute
- Add conditional edges based on route decision
- Keep the same behavior as the current LangChain router
- This demonstrates stateful agent architecture

---

### TASK 6 — Add Kubernetes Deployment Files
Create a `k8s/` folder with:

**`k8s/backend-deployment.yaml`**
- 2 replicas
- Resource limits (CPU: 500m, Memory: 512Mi)
- Load balancer service on port 80 → 5000
- Inject OPENAI_API_KEY from Kubernetes secret

**`k8s/frontend-deployment.yaml`**
- 2 replicas
- Load balancer service on port 80

---

### TASK 7 — Add GCP Setup Script
Create a `scripts/deploy-gcp.sh` bash script with step-by-step commands to:
1. Create GCP project
2. Enable required APIs (container, artifactregistry)
3. Create Artifact Registry repository
4. Build and push Docker images
5. Create GKE cluster
6. Create Kubernetes secrets
7. Apply k8s deployment files

---

### TASK 8 — Update README.md
Update the README with:
- Architecture diagram (text-based)
- Local development setup with Docker
- GCP deployment instructions
- Environment variables table
- LangSmith monitoring setup

---

## Folder Structure After All Tasks

```
yellowpages-chatbot/
├── backend/
│   ├── app.py
│   ├── agents/
│   │   ├── router_agent.py         ← upgrade to LangGraph
│   │   ├── search_agent.py
│   │   ├── knowledge_agent.py
│   │   └── polish_agent.py
│   ├── Dockerfile                  ← NEW (Task 1)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── Dockerfile                  ← NEW (Task 2)
│   └── package.json
├── k8s/                            ← NEW (Task 6)
│   ├── backend-deployment.yaml
│   └── frontend-deployment.yaml
├── scripts/                        ← NEW (Task 7)
│   └── deploy-gcp.sh
├── docker-compose.yml              ← NEW (Task 3)
├── .env.example                    ← UPDATE (Task 4)
└── README.md                       ← UPDATE (Task 8)
```

---

## Environment Variables Needed

```
# LLM
OPENAI_API_KEY=your_openai_key

# LangSmith Observability
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=yellowpages-chatbot

# App Config
FLASK_ENV=production
PORT=5000
```

---

## Priority Order
1. 🔴 Task 1 — Dockerfile backend (most critical)
2. 🔴 Task 4 — LangSmith (quick win, big interview impact)
3. 🔴 Task 5 — LangGraph router (biggest skill gap for the job)
4. 🟡 Task 2 — Dockerfile frontend
5. 🟡 Task 3 — docker-compose
6. 🟡 Task 6 — k8s files
7. 🟢 Task 7 — GCP deploy script
8. 🟢 Task 8 — README update

---

## Notes for AI Agent
- Do NOT change the existing business logic of the agents
- Keep all existing functionality working
- For LangGraph (Task 5), just rewrite the Router agent as a proof of concept
- All new files should follow existing code style
- Add comments explaining what each new piece does
