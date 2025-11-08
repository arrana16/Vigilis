import sys
import os
from dotenv import load_dotenv
from bson import ObjectId
from google.adk.agents.llm_agent import Tool

# Load environment variables
load_dotenv()

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import database and genai
from db import client
from google import genai

db = client["dispatch_db"]
collection = db["active_incidents"]
llm = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def update_context(id: str) -> str:
    """
    Retrieve the incident document from MongoDB and return it as a formatted string.
    """
    try:
        incident = collection.find_one({"_id": ObjectId(id)})
    except Exception as e:
        return f"Error querying incident with ID {id}: {e}"
    
    if not incident:
        return f"No incident found with ID: {id}"
    
    # Convert ObjectId to string for JSON serialization
    if "_id" in incident:
        incident["_id"] = str(incident["_id"])
    
    # Return the BSON document as a formatted string
    import json
    return json.dumps(incident, indent=2, default=str)

update_context_tool = Tool(func=update_context)