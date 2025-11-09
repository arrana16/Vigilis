from bson import ObjectId
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv
import ssl
import certifi

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# Create a new client and connect to the server with SSL certificate verification
# Use certifi for SSL certificate bundle
client = MongoClient(
    MONGO_URI, 
    server_api=ServerApi('1'),
    tlsCAFile=certifi.where()  # Use certifi's certificate bundle
)

db = client["dispatch_db"]
collection = db["active_incidents"]

def exists(id: str) -> bool:
    """
    Check if id entry exists in the database.
    
    Args:
        id: The incident ID to check
    
    Returns:
        True if the entry exists, False otherwise.
    
    Raises:
        ValueError: If there's an error querying the database
    """
    try:
        incident = collection.find_one({"incident_id": id})
        return incident is not None
    except Exception as e:
        raise ValueError(f"Error checking if incident {id} exists: {str(e)}")

def append_to_transcript(id: str, transcript: str, caller: str):
    """
    Update the transcript of an incident in the database.
    
    Args:
        id: The ID of the incident to update
        transcript: The new transcript text
        caller: The caller identifier (e.g., "911_call", "Patrol_12_comm")
    
    Raises:
        ValueError: If incident not found or update fails
    """
    try:
        addition = f"{caller}: {transcript}"
        result = collection.update_one(
            {"incident_id": id},
            {"$set": {f"transcripts.{caller}": addition}}
        )
        
        if result.matched_count == 0:
            raise ValueError(f"No incident found with ID: {id}")
            
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error appending transcript to incident {id}: {str(e)}")
    
def new_entry(id: str, transcript: str, caller: str):
    """
    Create a new incident entry in the database.
    
    Args:
        id: The ID of the new incident
        transcript: The initial transcript text
        caller: The caller identifier (e.g., "911_call", "Patrol_12_comm")
    
    Raises:
        ValueError: If incident creation fails or ID already exists
    """
    try:
        from datetime import datetime
        
        # Check if incident already exists
        if exists(id):
            raise ValueError(f"Incident with ID {id} already exists")
        
        entry = {
            "incident_id": id,
            "title": "",
            "severity": "",
            "status": "active",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "location": {
                "address_text": "",
                "geojson": {
                    "type": "Point",
                    "coordinates": []
                }
            },
            "transcripts": {
                caller: transcript
            },
            "current_summary": "",
            "last_summary_update_at": ""
        }

        collection.insert_one(entry)
        
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error creating new incident {id}: {str(e)}")


def retrieve_chat_elements(id: str) -> dict:
    """
    Retrieve the incident document from MongoDB and return chat_elements field as a dictionary.
    
    Args:
        id: The incident ID to retrieve from the database
    Returns:
        A dictionary containing chat_elements from the incident document 
    Raises:
        ValueError: If the incident is not found or database query fails
    """ 
    try:
        incident = collection.find_one({"incident_id": id})
    except Exception as e:
        raise ValueError(f"Error querying incident with ID {id}: {e}")
    
    if not incident:
        raise ValueError(f"No incident found with ID: {id}")
    
    # Get chat elements
    chat_elements = incident.get("chat_elements", {})
    
    # Build result dictionary
    result = {
        "chat_elements": chat_elements
    }
    
    return result

def update_chat_elements(id: str, chat_elements: dict):
    """
    Update the chat_elements field of an incident in the database.
    
    Args:
        id: The ID of the incident to update
        chat_elements: The new chat elements dictionary
    
    Raises:
        ValueError: If incident not found or update fails
    """
    try:
        result = collection.update_one(
            {"incident_id": id},
            {"$push": {"chat_elements": chat_elements}}
        )
        
        if result.matched_count == 0:
            raise ValueError(f"No incident found with ID: {id}")
            
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error updating chat elements for incident {id}: {str(e)}")

