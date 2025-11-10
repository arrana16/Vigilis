import sys
import os
from dotenv import load_dotenv
from datetime import datetime, UTC

# Load environment variables
load_dotenv()

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from db import client
from google.adk.tools import FunctionTool

# MongoDB setup
db = client["dispatch_db"]
collection = db["active_incidents"]


def get_dynamic_fields_func(id: str):
    """
    Retrieve specific dynamic fields from the incident BSON document.
    
    Args:
        id: The incident ID as a string to look up.
    Returns:
        Dictionary with transcripts (concatenated string), location, severity, summary, and coordinates.
    """
    try:
        # Query the incident directly (read concern not needed for single-server deployments)
        incident = collection.find_one({"incident_id": id})
    except Exception as e:
        return {"error": f"Error querying incident with ID {id}: {e}"}
    
    if not incident:
        return {"error": f"No incident found with ID: {id}"}
    
    # Get transcripts and concatenate all messages from all conversations
    transcripts_obj = incident.get("transcripts", {})
    all_transcripts = []
    for convo_key, messages in transcripts_obj.items():
        if isinstance(messages, list):
            all_transcripts.extend(messages)
        else:
            all_transcripts.append(str(messages))
    transcripts_str = " | ".join(all_transcripts)
    
    # Get current coordinates
    location_obj = incident.get("location", {})
    geojson = location_obj.get("geojson", {})
    current_coordinates = geojson.get("coordinates", [])
    
    # Build result dictionary
    result = {
        "title": incident.get("title", ""),
        "transcripts": transcripts_str,
        "location": location_obj.get("address_text", ""),
        "severity": incident.get("severity", ""),
        "summary": incident.get("current_summary", ""),
        "coordinates": current_coordinates
    }
    
    return result


def update_params_func(id: str, new_location: str, new_severity: str, new_summary: str, new_title: str, coordinates: list) -> dict:
    """
    Update the incident parameters in the database.
    Returns the updated document immediately after write.
    
    Args:
        id: The incident ID as a string
        new_location: The new location string to update to
        new_severity: The new severity string to update to
        new_summary: The new summary string to update to
        new_title: The new title string to update to
        coordinates: Optional list of [longitude, latitude] for geojson
    
    Returns:
        Dictionary with 'status', 'message', and 'incident' (the updated document)
    """
    try:
        # Build update document
        update_doc = {}
        
        if new_title:
            update_doc["title"] = new_title
        
        if new_location:
            update_doc["location.address_text"] = new_location
        
        if new_severity:
            update_doc["severity"] = new_severity.lower()
        
        if new_summary:
            update_doc["current_summary"] = new_summary
        
        # CRITICAL: Add coordinates to geojson.coordinates (use correct dot notation)
        # Check for None explicitly (not just falsy) because [0, 0] is valid
        if coordinates is not None:
            update_doc["location.geojson.coordinates"] = coordinates
            print(f"🗺️  Setting coordinates in update_doc: {coordinates} (type: {type(coordinates)})")
        
        # If any fields were updated, set the last_summary_update_at timestamp
        if update_doc:
            update_doc["last_summary_update_at"] = datetime.now(UTC).isoformat() + "Z"
        
        # Log what we're about to update
        print(f"📝 Update document being sent to MongoDB:")
        for key, value in update_doc.items():
            if key == "current_summary":
                print(f"   {key}: {str(value)[:100]}..." if len(str(value)) > 100 else f"   {key}: {value}")
            else:
                print(f"   {key}: {value}")
        
        # Use find_one_and_update to atomically update and return the document
        # This guarantees we get the updated version immediately
        from pymongo import ReturnDocument
        
        updated_incident = collection.find_one_and_update(
            {"incident_id": id},
            {"$set": update_doc},
            return_document=ReturnDocument.AFTER
        )
        
        if not updated_incident:
            return {
                "status": "error",
                "message": f"❌ No incident found with ID: {id}",
                "incident": None
            }
        
        # Success - we have the updated document
        coord_msg = f", Coordinates: {coordinates}" if coordinates is not None else ", Coordinates: unchanged"
        success_msg = f"✅ Successfully updated incident {id} - Location: {new_location}{coord_msg}, Severity: {new_severity}, Title: {new_title}"
        
        return {
            "status": "success",
            "message": success_msg,
            "incident": updated_incident
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ Error updating incident {id}: {e}",
            "incident": None
        }

