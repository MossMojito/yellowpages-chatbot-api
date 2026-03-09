"""
graph.py — LangGraph StateGraph Router

Replaces the manual if/elif routing in orchestrator.py with a proper
stateful directed graph. Each agent is a node; the router's decision
becomes a conditional edge that selects the next node.

Graph shape:
    START → classify → (conditional edge based on query_type)
                       ├─ business_search → polish → END
                       ├─ sports_knowledge → polish → END
                       └─ out_of_scope    → polish → END

Why LangGraph?
- State is typed (TypedDict) — no silent bugs from dict typos
- The pipeline is a real graph — easy to add new agents as new nodes
- Fully traceable in LangSmith — each node appears as a child span
- Industry-standard pattern for production multi-agent systems
"""

from typing import TypedDict, Literal

from langgraph.graph import StateGraph, END, START
from langsmith import traceable

from app.agents.router import query_router, out_of_scope_agent
from app.agents.search import business_search_agent
from app.agents.knowledge import sports_knowledge_agent
from app.agents.utils import polish_response


# ── Typed State ───────────────────────────────────────────────────────────────
class ChatState(TypedDict):
    """
    Shared state that flows through every node in the graph.
    Each node receives the full state and returns a partial dict
    to merge back — only the keys it updates need to be included.
    """
    user_input:   str   # the raw message from the user
    chat_history: str   # formatted conversation history
    query_type:   str   # set by classify node: business_search | sports_knowledge | out_of_scope
    response:     str   # built up by the agent node, polished by polish node


# ── Node Functions ────────────────────────────────────────────────────────────
# Each node is a plain Python function: (state) → dict of updated keys.
# LangGraph merges the returned dict back into the shared state.

def classify_node(state: ChatState) -> dict:
    """
    Calls query_router() to classify the intent.
    Sets state['query_type'] which drives the conditional edge below.
    """
    query_type = query_router(state["user_input"], state["chat_history"])
    print(f"🎯 Graph route: {query_type}")
    return {"query_type": query_type}


def business_search_node(state: ChatState) -> dict:
    """RAG agent: searches FAISS and generates a Thai response."""
    print("🔍 Graph node: Business Search")
    response = business_search_agent(state["user_input"], state["chat_history"])
    return {"response": response}


def sports_knowledge_node(state: ChatState) -> dict:
    """LLM agent: answers sports/fitness knowledge questions."""
    print("🧠 Graph node: Sports Knowledge")
    response = sports_knowledge_agent(state["user_input"], state["chat_history"])
    return {"response": response}


def out_of_scope_node(state: ChatState) -> dict:
    """Politely declines non-sports queries."""
    print("⚠️ Graph node: Out of Scope")
    response = out_of_scope_agent(state["user_input"])
    return {"response": response}


def polish_node(state: ChatState) -> dict:
    """Final node: makes the response warm and conversational."""
    print("✨ Graph node: Polish")
    polished = polish_response(
        state["response"],
        state["user_input"],
        state["chat_history"]
    )
    return {"response": polished}


# ── Routing Function ──────────────────────────────────────────────────────────
def route_after_classify(
    state: ChatState,
) -> Literal["business_search", "sports_knowledge", "out_of_scope"]:
    """
    Called after classify_node to decide which agent node runs next.
    Must return a value that matches one of the keys in add_conditional_edges().
    Falls back to out_of_scope for unexpected values.
    """
    qt = state.get("query_type", "out_of_scope").strip().lower()
    if qt in ("business_search", "sports_knowledge"):
        return qt
    return "out_of_scope"


# ── Build & Compile ───────────────────────────────────────────────────────────
def build_chat_graph() -> "CompiledGraph":  # type: ignore[name-defined]
    """
    Constructs the StateGraph, adds nodes + edges, and compiles it.
    The compiled graph is a LangChain Runnable — call .invoke(state_dict).
    """
    graph = StateGraph(ChatState)

    # Register nodes
    graph.add_node("classify",         classify_node)
    graph.add_node("business_search",  business_search_node)
    graph.add_node("sports_knowledge", sports_knowledge_node)
    graph.add_node("out_of_scope",     out_of_scope_node)
    graph.add_node("polish",           polish_node)

    # Entry point
    graph.add_edge(START, "classify")

    # Conditional branching after classify
    graph.add_conditional_edges(
        "classify",
        route_after_classify,
        {
            "business_search":  "business_search",
            "sports_knowledge": "sports_knowledge",
            "out_of_scope":     "out_of_scope",
        },
    )

    # All agent nodes converge on the polish node, then end
    graph.add_edge("business_search",  "polish")
    graph.add_edge("sports_knowledge", "polish")
    graph.add_edge("out_of_scope",     "polish")
    graph.add_edge("polish", END)

    return graph.compile()


# Module-level singleton — compiled once at import time
chat_graph = build_chat_graph()
