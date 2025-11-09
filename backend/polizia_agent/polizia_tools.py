import sys
import os
from dotenv import load_dotenv
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


def get_incident_context(incident_id: str) -> str:
   """
   Retrieve detailed incident information from the database.
  
   Use this tool when the user asks questions about:
   - Incident location or address 
   - Current incident status or summary
   - Transcripts from 911 calls or radio communications
   - Timeline of events
   - Incident severity or type
   - Any other details about a specific incident
  
   Args:
       incident_id: The ID of the incident to retrieve (e.g., "INC-001" or UUID format)
      
   Returns:
       A JSON string containing complete incident details including location, transcripts,
       status, severity, and timeline information
   """
   try:
       incident = collection.find_one({"incident_id": incident_id})
   except Exception as e:
       return json.dumps({
           "error": f"Database error: {str(e)}",
           "incident_id": incident_id
       })
  
   if not incident:
       return json.dumps({
           "error": f"No incident found with ID: {incident_id}",
           "incident_id": incident_id
       })
  
   # Convert ObjectId to string for JSON serialization
   if "_id" in incident:
       incident["_id"] = str(incident["_id"])
  
   # Return the BSON document as a formatted string
   return json.dumps(incident, indent=2, default=str)