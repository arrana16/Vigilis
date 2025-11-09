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
        incident = collection.find_one({"incident_id": id})
    except Exception as e:
        return {"error": f"Error querying incident with ID {id}: {e}"}
    
    if not incident:
        return {"error": f"No incident found with ID: {id}"}
    
    # Get transcripts and concatenate into "key:value, key:value..." format
    transcripts_obj = incident.get("transcripts", {})
    transcripts_str = ", ".join([f"{key}:{value}" for key, value in transcripts_obj.items()])
    
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


def update_params_func(id: str, new_location: str, new_severity: str, new_summary: str, new_title: str, coordinates: list = None) -> str:
    """
    Update the incident parameters in the database.
    
    Args:
        id: The incident ID as a string
        new_location: The new location string to update to
        new_severity: The new severity string to update to
        new_summary: The new summary string to update to
        new_title: The new title string to update to
        coordinates: Optional list of [longitude, latitude] for geojson
    
    Returns:
        Confirmation message as a string
    """
    try:
        # Build update document
        update_doc = {
            **({"title": new_title} if new_title else {}),
            **({"location.address_text": new_location} if new_location else {}),
            **({"severity": new_severity.lower()} if new_severity else {}),
            **({"current_summary": new_summary} if new_summary else {})
        }
        
        # Add coordinates to geojson if provided
        if coordinates and len(coordinates) == 2:
            update_doc["location.geojson"] = {
                "type": "Point",
                "coordinates": coordinates
            }
        
        # If any fields were updated, set the last_summary_update_at timestamp
        if update_doc:
            update_doc["last_summary_update_at"] = datetime.now(UTC).isoformat() + "Z"
        
        # Update the incident in MongoDB
        result = collection.update_one(
            {"incident_id": id},
            {"$set": update_doc}
        )
        
        if result.matched_count == 0:
            return f"❌ No incident found with ID: {id}"
        
        coord_msg = f", Coordinates: {coordinates}" if coordinates else ""
        return f"✅ Successfully updated incident {id} - Location: {new_location}{coord_msg}, Severity: {new_severity}, Summary updated"
        
    except Exception as e:
        return f"❌ Error updating incident {id}: {e}"

