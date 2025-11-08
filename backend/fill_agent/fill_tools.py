import sys
import os
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from db import client
from google import genai
from google.genai import types

db = client["dispatch_db"]
collection = db["active_incidents"]
knowledge_base = db["incident_knowledge_base"]
llm = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# MongoDB setup
db = client["dispatch_db"]
collection = db["active_incidents"]


def get_dynamic_fields(id: str):
    """
    Retrieve specific dynamic fields from the incident BSON document.
    
    Args:
        id: The incident ID as a string to look up.
    Returns:
        Dictionary with transcripts (concatenated string), location, severity, and summary.
    Raises:
        ValueError: If the incident is not found.
    """
    try:
        incident = collection.find_one({"_id": ObjectId(id)})
    except Exception as e:
        raise ValueError(f"Error querying incident with ID {id}: {e}")
    
    if not incident:
        raise ValueError(f"No incident found with ID: {id}")
    
    # Get transcripts and concatenate into "key:value, key:value..." format
    transcripts_obj = incident.get("transcripts", {})
    transcripts_str = ", ".join([f"{key}:{value}" for key, value in transcripts_obj.items()])
    
    # Build result dictionary
    result = {
        "transcripts": transcripts_str,
        "location": incident.get("location", {}).get("address_text", ""),
        "severity": incident.get("severity", ""),
        "summary": incident.get("current_summary", "")
    }
    
    return result


def update_params(id: str, new_location: str, new_severity: str, new_summary: str) -> str:
    """
    Update the incident parameters in the database.
    
    Args:
        id: The incident ID as a string
        new_location: The new location string to update to
        new_severity: The new severity string to update to
        new_summary: The new summary string to update to
    
    Returns:
        Confirmation message as a string
    
    Raises:
        ValueError: If the incident is not found or update fails
    """
    try:
        from datetime import datetime
        
        # Build update document



        update_doc = {
            **({"location.address_text": new_location} if new_location else {}),
            **({"severity": new_severity.lower()} if new_severity else {}),
            **({"current_summary": new_summary} if new_summary else {}),
            **({"last_summary_update_at": datetime.utcnow().isoformat() + "Z"} if new_summary else {})
        }
        
        # Update the incident in MongoDB
        result = collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_doc}
        )
        
        if result.matched_count == 0:
            raise ValueError(f"No incident found with ID: {id}")
        
        return f"✅ Successfully updated incident {id} - Location: {new_location}, Severity: {new_severity}, Summary updated"
        
    except Exception as e:
        raise ValueError(f"Error updating incident {id}: {e}")
