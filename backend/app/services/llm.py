from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from app.core.config import Config

# ── LLM ───────────────────────────────────────────────────────────────────────
llm = ChatOpenAI(
    model=Config.LLM_MODEL,
    temperature=Config.TEMPERATURE,
    openai_api_key=Config.OPENAI_API_KEY
)

# ── Embeddings ────────────────────────────────────────────────────────────────
embeddings = OpenAIEmbeddings(
    model=Config.EMBEDDING_MODEL,
    openai_api_key=Config.OPENAI_API_KEY
)

# ── FAISS vectorstore ─────────────────────────────────────────────────────────
try:
    vectorstore = FAISS.load_local(
        Config.VECTORSTORE_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )
    print(f"📊 Vectorstore loaded: {vectorstore.index.ntotal} vectors")
except Exception as e:
    print(f"⚠️ Error loading vectorstore: {e}")
    vectorstore = None


# ── Simple conversation memory ────────────────────────────────────────────────
# ConversationBufferWindowMemory was moved/deprecated in LangChain 0.3.x.
# This lightweight replacement exposes the same interface (load_memory_variables
# and save_context) that the orchestrator relies on, with no external dependency.
class SimpleMemory:
    """Sliding-window conversation memory — keeps the last `k` message pairs."""

    def __init__(self, k: int = 3):
        self.k = k
        self._history: list[dict] = []  # list of {"type": "human"/"ai", "content": str}

    def load_memory_variables(self, _inputs: dict) -> dict:
        return {"chat_history": list(self._history)}

    def save_context(self, inputs: dict, outputs: dict) -> None:
        self._history.append({"type": "human", "content": inputs.get("input", "")})
        self._history.append({"type": "ai", "content": outputs.get("output", "")})
        # Keep only the last k * 2 messages (k pairs)
        self._history = self._history[-(self.k * 2):]


def get_memory() -> SimpleMemory:
    return SimpleMemory(k=3)


# Global single-session memory (demo mode — not thread-safe for multi-user)
global_memory = get_memory()
