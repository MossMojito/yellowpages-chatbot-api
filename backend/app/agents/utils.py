from langsmith import traceable
from app.services.llm import llm

@traceable(name="Agent — polish response", run_type="chain")
def polish_response(raw_response: str, user_query: str, chat_history: str = "") -> str:
    """
    Makes responses more natural and conversational.
    Traced in LangSmith as 'Agent — polish response'.
    """
    
    prompt = f"""You are a friendly sports facility assistant.

**IMPORTANT: Use "ค่ะ" (female politeness) NOT "ครับ"**

Conversation history:
{chat_history}

User asked: "{user_query}"

Raw response: {raw_response}

Rewrite this to be:
1. More natural and conversational
2. Warm and friendly
3. Helpful and engaging
4. Like talking to a real female person
5. Use "ค่ะ" consistently

Keep all the factual information but make it sound human and female!
"""
    
    polished = llm.invoke(prompt).content
    return polished
