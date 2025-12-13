from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

app = Flask(__name__)
CORS(app)

# Initialize OpenAI
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, api_key=OPENAI_API_KEY)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=OPENAI_API_KEY)

# Load FAISS vectorstore
vectorstore = FAISS.load_local(
    "yellowpages_vectorstore",
    embeddings,
    allow_dangerous_deserialization=True
)

# Initialize memory
memory = ConversationBufferWindowMemory(k=3, return_messages=True)

# Router Agent
def route_query(query):
    """Classify user intent"""
    router_prompt = PromptTemplate(
        input_variables=["query"],
        template="""คุณเป็น Query Router สำหรับระบบค้นหาสถานที่ออกกำลังกาย
        
ประเภทคำถาม:
1. business_search: ถ้าถามหา/ต้องการสถานที่เฉพาะ (มีชื่อสถานที่, ทำเล, ประเภทกีฬา)
2. knowledge: ถ้าถามเกี่ยวกับกีฬาทั่วไป (ประโยชน์, วิธีเล่น, ความรู้)
3. exploration: ถ้าถาม "มีอะไรบ้าง", "แนะนำหน่อย"
4. out_of_scope: ถ้าไม่เกี่ยวกับกีฬาหรือสถานที่เลย

คำถาม: {query}

ตอบเพียง: business_search, knowledge, exploration, หรือ out_of_scope"""
    )
    
    chain = LLMChain(llm=llm, prompt=router_prompt)
    route = chain.run(query=query).strip().lower()
    return route

# Business Search Agent
def search_business(query):
    """Search for sports facilities"""
    # Get chat history
    history = memory.load_memory_variables({})
    context = history.get('history', '')
    
    # Check if query uses pronouns (refers to previous context)
    pronoun_keywords = ['ที่แรก', 'ที่สอง', 'ที่สาม', 'ที่นี่', 'ที่นั่น', 'แห่งนั้น', 'แห่งนี้']
    uses_pronoun = any(kw in query for kw in pronoun_keywords)
    
    if uses_pronoun and context:
        # Use context from memory
        search_query = f"{context}\n{query}"
    else:
        # Fresh search
        search_query = query
    
    # Search vectorstore
    results = vectorstore.similarity_search(search_query, k=10)
    
    # Location validation
    location_keywords = ['กรุงเทพ', 'bangkok', 'นนทบุรี', 'ปทุมธานี', 'สมุทรปราการ']
    filtered_results = []
    
    for r in results:
        metadata = r.metadata
        address = metadata.get('address', '').lower()
        
        # Check if location matches
        if any(loc in query.lower() for loc in location_keywords):
            if any(loc in address for loc in location_keywords):
                filtered_results.append(r)
        else:
            filtered_results.append(r)
    
    # If no results after filtering, use original
    if not filtered_results:
        filtered_results = results[:3]
    else:
        filtered_results = filtered_results[:3]
    
    # Format results
    if not filtered_results:
        return "ขออภัยค่ะ ยังไม่มีข้อมูลในระบบ 🙏"
    
    response = f"สวัสดีค่ะ! 😊 ดิฉันมีคำแนะนำสถานที่ออกกำลังกายให้ค่ะ:\n\n"
    
    for idx, doc in enumerate(filtered_results, 1):
        m = doc.metadata
        response += f"{idx}. **{m.get('name', 'N/A')}**\n"
        response += f"   ตั้งอยู่ที่ {m.get('address', 'N/A')} ค่ะ\n"
        if m.get('tel'):
            response += f"   โทร {m.get('tel')} ค่ะ\n"
        response += "\n"
    
    response += "หากคุณต้องการรายละเอียดเพิ่มเติมหรือมีคำถามอื่น สามารถถามดิฉันได้เลยนะคะ 💪✨"
    
    return response

# Knowledge Agent
def answer_knowledge(query):
    """Answer general sports questions"""
    knowledge_prompt = PromptTemplate(
        input_variables=["query"],
        template="""คุณเป็นผู้เชี่ยวชาญด้านกีฬาและการออกกำลังกาย ตอบคำถามเป็นภาษาไทย
        
คำถาม: {query}

ตอบแบบเป็นกันเอง ใช้ "ค่ะ" สั้นๆ กระชับ ไม่เกิน 5 ประโยค"""
    )
    
    chain = LLMChain(llm=llm, prompt=knowledge_prompt)
    response = chain.run(query=query)
    return response

# Exploration Agent
def explore_categories():
    """Show available categories"""
    response = """สวัสดีค่ะ! 😊 เรามีสถานที่ออกกำลังกายหลากหลายประเภทให้เลือกค่ะ:

🏃‍♀️ **ยอดนิยม:**
- โยคะ (Yoga)
- ฟิตเนส (Fitness Center)
- มวยไทย (Muay Thai)

⚽ **กีฬาทีม:**
- ฟุตบอล (Football)
- แบดมินตัน (Badminton)
- วอลเลย์บอล (Volleyball)

🏊‍♂️ **กีฬาน้ำ:**
- สระว่ายน้ำ (Swimming Pool)

🎯 **อื่นๆ:**
- เทนนิส, กอล์ฟ, ยิงปืน, ปีนหน้าผา

คุณสนใจประเภทไหนคะ? หรือจะระบุทำเลที่ต้องการเลยก็ได้ค่ะ! 💪"""
    
    return response

# Out of Scope Agent
def handle_out_of_scope():
    """Handle unrelated queries"""
    return """ขออภัยค่ะ 🙏 ดิฉันเป็นผู้ช่วยค้นหาสถานที่ออกกำลังกายและกีฬาเท่านั้นค่ะ 
    
คุณสามารถถามดิฉันเกี่ยวกับ:
- สถานที่ออกกำลังกาย (โยคะ, ฟิตเนส, สระว่ายน้ำ)
- ประโยชน์ของกีฬาแต่ละประเภท
- คำแนะนำสถานที่ในพื้นที่ต่างๆ

มีอะไรให้ช่วยเหลือเกี่ยวกับกีฬาไหมคะ? 😊"""

# Response Polish Agent
def polish_response(response, query):
    """Make response more natural"""
    # Add emojis and friendly tone
    if "ยังไม่มีข้อมูล" not in response:
        # Already polished in individual agents
        return response
    return response

# Main Chatbot Function
def chatbot(user_message):
    """Main chatbot orchestrator"""
    try:
        # Route query
        route = route_query(user_message)
        
        # Execute appropriate agent
        if 'business' in route:
            response = search_business(user_message)
        elif 'knowledge' in route:
            response = answer_knowledge(user_message)
        elif 'exploration' in route:
            response = explore_categories()
        else:
            response = handle_out_of_scope()
        
        # Polish response
        final_response = polish_response(response, user_message)
        
        # Save to memory
        memory.save_context(
            {"input": user_message},
            {"output": final_response}
        )
        
        return final_response
        
    except Exception as e:
        return f"ขออภัยค่ะ เกิดข้อผิดพลาด: {str(e)} 🙏"

# API Routes
@app.route('/', methods=['GET'])
def health():
    return jsonify({
        'status': 'Chatbot API is running!',
        'service': 'Yellow Pages Sports Chatbot',
        'version': '1.0'
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
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
