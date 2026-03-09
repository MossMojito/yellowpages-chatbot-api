from langsmith import traceable
from app.services.llm import llm

@traceable(name="Router — classify query", run_type="chain")
def query_router(user_query: str, chat_history: str = "") -> str:
    """
    Agent that decides query type based on user intent.
    Traced in LangSmith as 'Router — classify query'.
    """
    
    prompt = f"""You are a query classifier for a sports facility chatbot.

Conversation history:
{chat_history}

Current query: "{user_query}"

Classify into ONE category:

1. business_search
   - User wants to FIND/LOCATE businesses or places
   - Examples: "find gym", "swimming pools near me", "show me yoga studios"
   
2. sports_knowledge  
   - User wants INFORMATION/ADVICE about sports or fitness
   - Examples: "how to swim better", "benefits of yoga", "muay thai for beginners"
   
3. out_of_scope
   - NOT related to sports or fitness at all
   - Examples: "weather today", "cook pasta", "stock prices"

Consider the conversation history for context.

Return ONLY ONE WORD: business_search, sports_knowledge, or out_of_scope
"""
    
    response = llm.invoke(prompt)
    return response.content.strip().lower()

@traceable(name="Agent — out of scope", run_type="chain")
def out_of_scope_agent(query: str) -> str:
    """
    Agent that politely handles non-sports queries.
    Traced in LangSmith as 'Agent — out of scope'.
    """
    
    prompt = f"""User asked something not related to sports: "{query}"

You are a female assistant.
**IMPORTANT: Use "ค่ะ" (female) NOT "ครับ"**

Write a brief, friendly response that:
1. Politely declines to answer
2. Reminds them you specialize in sports/fitness
3. Suggests what you CAN help with

Keep it friendly and short (2-3 sentences).
Female Thai tone with "ค่ะ"!
"""
    
    response = llm.invoke(prompt)
    return response.content
