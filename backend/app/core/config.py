import os

class Config:
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is required!")
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    VECTORSTORE_PATH = os.path.join(BASE_DIR, "data", "vectorstore")
    
    # Model Config
    LLM_MODEL = "gpt-4o-mini"
    EMBEDDING_MODEL = "text-embedding-3-small"
    TEMPERATURE = 0.7
