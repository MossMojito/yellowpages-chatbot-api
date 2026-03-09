"""
orchestrator.py — Main chatbot entrypoint

The manual if/elif routing is replaced by invoking the LangGraph StateGraph
defined in graph.py. The orchestrator now just:
  1. Builds the initial state (user input + chat history)
  2. Calls chat_graph.invoke(state)
  3. Saves the result to memory
  4. Returns the final response

All agent logic and routing lives in graph.py.
"""

from langsmith import traceable
from app.services.llm import get_memory, global_memory
from app.agents.graph import chat_graph


@traceable(name="Chatbot — full pipeline (LangGraph)", run_type="chain")
def chatbot(user_input: str) -> str:
    """
    CONVERSATIONAL multi-agent chatbot powered by LangGraph.

    The request flows through a StateGraph:
        START → classify → (conditional) → agent_node → polish → END

    Every node is a child span in LangSmith.
    """

    # ── Build chat history from memory ────────────────────────────────────────
    history = global_memory.load_memory_variables({})
    chat_history = ""
    if history.get("chat_history"):
        for msg in history["chat_history"]:
            chat_history += f"{msg['type']}: {msg['content']}\n"

    print(f"💭 User: {user_input}")
    print(f"🧠 Memory: {len(history.get('chat_history', []))} messages")

    # ── Invoke the LangGraph ───────────────────────────────────────────────────
    # The graph handles routing + agent selection + polish internally.
    # We just supply the initial state and get the final state back.
    final_state = chat_graph.invoke({
        "user_input":   user_input,
        "chat_history": chat_history,
        "query_type":   "",   # will be set by classify_node
        "response":     "",   # will be set by agent node + polish node
    })

    response = final_state["response"]

    # ── Save result to sliding-window memory ──────────────────────────────────
    global_memory.save_context(
        {"input": user_input},
        {"output": response}
    )
    print("💾 Saved to memory")
    print("=" * 60)

    return response
