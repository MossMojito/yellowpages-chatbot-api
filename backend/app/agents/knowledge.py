from langsmith import traceable
from app.services.llm import llm
from app.agents.search import business_search_agent

@traceable(name="Agent — sports knowledge", run_type="chain")
def sports_knowledge_agent(query: str, chat_history: str = "") -> str:
    """
    Agent that provides sports/fitness advice using LLM knowledge.
    """
    
    prompt = f"""You are a knowledgeable female sports and fitness expert.

**IMPORTANT: Respond as female - use "ค่ะ" NOT "ครับ"**

Conversation history:
{chat_history}

User question: "{query}"

Provide helpful, practical advice:
- Clear, actionable information
- 3-5 key points
- Keep it concise (150-200 words)
- Be encouraging and supportive
- Use female Thai politeness (ค่ะ)

If relevant, mention that they can find facilities/trainers in our database.
"""
    
    response = llm.invoke(prompt)
    knowledge = response.content
    
    # Check if we should also suggest businesses
    suggest_prompt = f"""User asked: "{query}"

Should I also suggest relevant sports facilities/businesses?
Answer ONLY: yes or no
"""
    
    should_suggest = llm.invoke(suggest_prompt).content.strip().lower()
    
    if "yes" in should_suggest:
        # Add business suggestions
        businesses = business_search_agent(query, chat_history)
        knowledge += f"\n\n---\n\n**สถานที่ที่แนะนำค่ะ:**\n\n{businesses}"
    
    return knowledge
