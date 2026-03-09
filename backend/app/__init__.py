import os
import logging
from flask import Flask
from flask_cors import CORS
from app.api.routes import api_bp

logger = logging.getLogger(__name__)

def _init_langsmith():
    """
    Initialize LangSmith tracing.
    LangChain 0.3.x automatically traces all LLM calls when these env vars are set:
      LANGCHAIN_TRACING_V2=true
      LANGCHAIN_API_KEY=<your key>
      LANGCHAIN_PROJECT=yellowpages-chatbot
    No code-level wrapping needed — tracing is active as soon as env vars exist.
    """
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    project = os.getenv("LANGCHAIN_PROJECT", "yellowpages-chatbot")

    if tracing_enabled:
        if not os.getenv("LANGCHAIN_API_KEY"):
            logger.warning("⚠️  LANGCHAIN_TRACING_V2=true but LANGCHAIN_API_KEY is not set — tracing disabled.")
        else:
            logger.info(f"🔭 LangSmith tracing ENABLED  |  project: '{project}'")
    else:
        logger.info("🔭 LangSmith tracing DISABLED (set LANGCHAIN_TRACING_V2=true to enable)")

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Initialize LangSmith observability (reads from environment variables)
    _init_langsmith()

    # Register Blueprints
    app.register_blueprint(api_bp)

    return app
