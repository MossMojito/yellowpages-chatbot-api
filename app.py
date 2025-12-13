import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_classic.memory import ConversationBufferWindowMemory

# ==========================================
# Configuration
# ==========================================

# Get OpenAI API key from environment variable
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required!")

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    openai_api_key=OPENAI_API_KEY
)

# Initialize Embeddings
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_key=OPENAI_API_KEY
)

# Load FAISS vectorstore from disk
vectorstore_path = os.path.join(os.path.dirname(__file__), "yellowpages_vectorstore")
vectorstore = FAISS.load_local(
    vectorstore_path,
    embeddings,
    allow_dangerous_deserialization=True
)

# Initialize Memory
memory = ConversationBufferWindowMemory(
    memory_key="chat_history",
    k=3,  # Remember last 3 exchanges
    return_messages=True,
    input_key="input",
    output_key="output"
)

print("✅ Configuration loaded!")
print(f"🤖 LLM: {llm.model_name}")
print(f"📊 Vectorstore: {vectorstore.index.ntotal} vectors")

# ==========================================
# Agent Functions
# ==========================================

def query_router(user_query: str, chat_history: str = "") -> str:
    """
    Agent that decides query type based on user intent.
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


def business_search_agent(query: str, chat_history: str = "") -> str:
    """
    Conversational business search - talks like a human!
    """
    
    # Extract search context
    context_prompt = f"""Based on conversation history:
{chat_history}

Current query: "{query}"

Extract:
1. Location mentioned (city, area, district)
2. Sport/activity type
3. Any other requirements

Return as: location: X, sport: Y, requirements: Z
If nothing mentioned, say: none
"""
    
    context_info = llm.invoke(context_prompt).content
    print(f"📍 Context: {context_info}")
    
    # Enhanced search query
    search_query = f"{query} {context_info}"
    
    # Search database
    results = vectorstore.similarity_search(search_query, k=5)
    
    if not results:
        return "ขออภัยค่ะ ยังไม่มีข้อมูลในระบบ 🙏"
    
    # Format results
    results_text = ""
    for i, doc in enumerate(results, 1):
        m = doc.metadata
        results_text += f"""
{i}. {m.get('name', 'N/A')}
   ตั้งอยู่ที่ {m.get('address', 'N/A')} 
   โทร {m.get('phone', 'N/A')}
   
"""
    
    # Natural response
    natural_response_prompt = f"""User asked: "{query}"

Conversation history:
{chat_history}

Search results:
{results_text}

Write a warm, conversational Thai response like a helpful female assistant:
**IMPORTANT: Use female Thai politeness - use "ค่ะ" NOT "ครับ"**

1. Acknowledge their request naturally
2. Present the businesses in a friendly way
3. Offer to help with more details
4. Be natural and conversational

Include the business details but make it flow naturally.
"""
    
    response = llm.invoke(natural_response_prompt).content
    return response


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


def out_of_scope_agent(query: str) -> str:
    """
    Agent that politely handles non-sports queries.
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


def polish_response(raw_response: str, user_query: str, chat_history: str = "") -> str:
    """
    Makes responses more natural and conversational
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


def chatbot(user_input: str) -> str:
    """
    CONVERSATIONAL multi-agent chatbot - talks like a human!
    """
    
    # Get history
    history = memory.load_memory_variables({})
    chat_history = ""
    
    if history.get('chat_history'):
        for msg in history['chat_history']:
            chat_history += f"{msg.type}: {msg.content}\n"
    
    print(f"💭 User: {user_input}")
    print(f"🧠 Memory: {len(history.get('chat_history', []))} messages")
    
    # Route query
    query_type = query_router(user_input, chat_history)
    print(f"🎯 Route: {query_type}")
    
    # Execute agent
    if query_type == "business_search":
        print("🔍 Agent: Business Search (Conversational RAG)")
        response = business_search_agent(user_input, chat_history)
        
    elif query_type == "sports_knowledge":
        print("🧠 Agent: Sports Knowledge (LLM)")
        response = sports_knowledge_agent(user_input, chat_history)
        
    elif query_type == "out_of_scope":
        print("⚠️ Agent: Out-of-Scope")
        response = out_of_scope_agent(user_input)
        
    else:
        response = "I'm not sure how to help with that. Could you rephrase?"
    
    # Polish response for naturalness
    response = polish_response(response, user_input, chat_history)
    
    # Save to memory
    memory.save_context(
        {"input": user_input},
        {"output": response}
    )
    
    print("💾 Saved to memory")
    print("="*60)
    
    return response


# ==========================================
# Flask API
# ==========================================

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def health():
    return jsonify({
        'status': 'Chatbot API is running!',
        'service': 'Yellow Pages Sports Chatbot',
        'version': '1.0',
        'vectorstore_size': vectorstore.index.ntotal
    })

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Get chatbot response
        response = chatbot(message)
        
        return jsonify({'response': response})
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
