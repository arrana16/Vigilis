import sys
import os
from dotenv import load_dotenv
from bson import ObjectId
import json

# Load environment variables
load_dotenv()

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import database
from db import client

db = client["dispatch_db"]
collection = db["active_incidents"]

def update_context(id: str) -> str:
    """
    Retrieve the incident document from MongoDB and return it as a formatted string.
    
    Args:
        id: The incident ID to retrieve from the database
        
    Returns:
        A JSON string containing the full incident document with all details
        
    Raises:
        ValueError: If incident is not found or database query fails
    """
    try:
        incident = collection.find_one({"_id": ObjectId(id)})
    except Exception as e:
        raise ValueError(f"Error querying incident with ID {id}: {e}")
    
    if not incident:
        raise ValueError(f"No incident found with ID: {id}")
    
    # Convert ObjectId to string for JSON serialization
    if "_id" in incident:
        incident["_id"] = str(incident["_id"])
    
    # Return the BSON document as a formatted string
    return json.dumps(incident, indent=2, default=str)