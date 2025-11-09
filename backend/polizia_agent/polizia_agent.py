import sys
import os
from dotenv import load_dotenv
from datetime import datetime, UTC

# Handle imports for both direct execution and module import
try:
    from backend.db import update_chat_elements
    from .polizia_tools import update_context, update_context_func
except ImportError:
    # Add parent directory to path for direct execution
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    from db import update_chat_elements
    from polizia_agent.polizia_tools import update_context, update_context_func

from google.adk.agents.llm_agent import Agent

load_dotenv()

# Force API key mode (not Vertex AI)
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = '0'

# System instruction for the agent
SYSTEM_INSTRUCTION = """You are Vigilis, an AI assistant for 911 dispatchers and emergency services personnel. 

Your role is to:
- Help dispatchers understand current incidents by retrieving and explaining incident data
- Answer questions about emergency protocols and procedures
- Provide context and insights about ongoing situations
- Assist with incident management decisions

You have access to a tool called 'update_context_func' that can retrieve incident information from the database. When a user asks about a specific incident, use this tool to get the latest data.

Be professional, concise, and helpful. Your goal is to support emergency services personnel in making fast, informed decisions."""

# Create the polizia agent
polizia_agent = Agent(
    model='gemini-2.5-flash',
    name='vigilis_assistant',
    description='AI assistant for 911 dispatchers and emergency services personnel.',
    instruction=SYSTEM_INSTRUCTION,
    tools=[update_context]
)


