# 📓 Docker Concepts & Project Fixes — Study Notes

## 1. Docker Concepts: Dockerfile → Image → Container → docker-compose

```
Dockerfile          →        Image          →       Container
(recipe)                  (cooked meal)             (running meal)
```

| Term | What it is | Analogy |
|---|---|---|
| **Dockerfile** | Step-by-step instructions to build an app environment | Recipe |
| **Image** | The built, static snapshot of that environment | Frozen meal |
| **Container** | A running instance of an image | Heated & served meal |
| **docker-compose** | Tool that runs multiple containers together | Restaurant kitchen |

---

## 2. How docker-compose.yml Connects Everything

```
docker-compose.yml
│
├── backend:
│   ├── build: ./backend         → reads backend/Dockerfile → builds image
│   ├── ports: "5001:5000"       → Mac port 5001 → container port 5000
│   ├── env_file: .env           → passes OPENAI_API_KEY into the container
│   └── volumes: ./backend:/app  → your local code files live inside the container
│
└── frontend:
    ├── build: ./frontend                    → reads frontend/Dockerfile → builds image
    ├── ports: "3001:80"                     → Mac port 3001 → nginx inside container port 80
    └── volumes: nginx-local.conf → /etc/... → replaces default nginx config
```

### Key docker-compose Commands

| Command | What it does |
|---|---|
| `docker compose up --build` | Build images + start all containers |
| `docker compose up -d` | Start in background (detached) |
| `docker compose down` | Stop and remove containers |
| `docker compose ps` | See running containers and their status |
| `docker compose logs backend --tail=30` | See last 30 lines of backend logs |

---

## 3. Local vs GCP Workflow

```
❌ Old (slow, expensive):
Fix bug → docker buildx build → push to GCP → kubectl rollout restart → wait 2-3 min → test

✅ New (fast, free):
Fix bug → docker compose up --build → test on localhost in ~10 sec → push to GCP once when working
```

| | docker-compose (local) | Kubernetes (GCP) |
|---|---|---|
| Purpose | Develop & debug | Production |
| Rebuild speed | ~10 seconds | ~2-3 minutes |
| Cost | Free (your laptop) | GCP credits |
| URL | localhost:3001 / localhost:5001 | 34.87.8.226 / 34.126.130.198 |

---

## 4. Bugs We Fixed in This Project

### Bug 1 — `routes.py`: Duplicate `health()` function
```python
# ❌ Bug: duplicate function name + @app doesn't exist in this file
@app.route('/health')
def health():
    return {'status': 'ok'}, 200

# ✅ Fix: one correct /health on the api_bp blueprint
@api_bp.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'vectorstore_loaded': True}), 200
```

### Bug 2 — `requirements.txt`: Wrong LangChain version
```
# ❌ Bug: FAISS index was saved with langchain 0.3.x (pydantic v2)
#         but we installed 0.2.x (pydantic v1) → __fields_set__ error
langchain==0.2.16
pydantic==1.10.21

# ✅ Fix: use the same version that created the FAISS index
langchain>=0.3.0
```

### Bug 3 — `llm.py`: Broken import
```python
# ❌ Bug: ConversationBufferWindowMemory was removed from langchain.memory in 0.3.x
from langchain.memory import ConversationBufferWindowMemory

# ✅ Fix: replaced with a custom SimpleMemory class (same interface, no dependency)
class SimpleMemory:
    def load_memory_variables(self, _): ...   # returns chat history
    def save_context(self, inputs, outputs): ... # saves new message pair
```

### Bug 4 — docker-compose healthcheck: curl not installed
```yaml
# ❌ Bug: python:3.11-slim doesn't include curl
test: ["CMD", "curl", "-f", "http://localhost:5000/health"]

# ✅ Fix: use Python's built-in urllib (always available)
test: ["CMD", "python", "-c",
       "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"]
```

---

## 5. Project Ports Reference

| Service | Local (docker-compose) | GCP (Kubernetes) |
|---|---|---|
| Frontend | `localhost:3001` | `34.87.8.226` |
| Backend API | `localhost:5001` | `34.126.130.198` |
| Backend health | `localhost:5001/health` | `34.126.130.198/health` |
| Backend chat | `localhost:5001/chat` (POST) | `34.126.130.198/chat` (POST) |

---

## 6. Environment Variables (`.env`)

| Variable | Required | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | ✅ Yes | GPT-4o-mini + embeddings |
| `LANGCHAIN_TRACING_V2` | Optional | Enable LangSmith tracing (`true`/`false`) |
| `LANGCHAIN_API_KEY` | Optional | LangSmith API key |
| `LANGCHAIN_PROJECT` | Optional | LangSmith project name |
