import sys
import os
from dotenv import load_dotenv
from bson import ObjectId
from suggest import summarize_current_status
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Force API key mode (not Vertex AI)
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = '0'

# Add parent directory to path to import from root-level agent.py
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import GeminiAgent from root directory, not from my_agent/agent.py
from db import client
from google import genai
from google.genai import types

db = client["dispatch_db"]
collection = db["active_incidents"]
knowledge_base = db["incident_knowledge_base"]
llm = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_report(id: str):
    try:
        incident = collection.find_one({"incident_id": id})
    except Exception as e:
        raise ValueError(f"Error querying incident with ID {id}: {e}")
    
    if not incident:
        raise ValueError(f"No incident found with ID: {id}")
    
    # Extract all relevant incident data
    incident_id = incident.get("incident_id", "N/A")
    status = incident.get("status", "N/A").upper()
    created_at = incident.get("created_at", "N/A")
    last_update = incident.get("last_summary_update_at", "N/A")
    
    # Extract location details
    location = incident.get("location", {})
    address = location.get("address_text", "N/A")
    geojson = location.get("geojson", {})
    coords = geojson.get("coordinates", [])
    
    # Extract transcripts
    transcripts = incident.get("transcripts", {})
    current_summary = incident.get("current_summary", "N/A")
    
    # Format all available transcript data
    call_911 = transcripts.get("911_call", "No 911 call transcript available.")
    patrol_comm = transcripts.get("Patrol_12_comm", "No patrol communications available.")
    engine_comm = transcripts.get("Engine_01_comm", "No engine communications available.")
    
    prompt = f"""Generate a comprehensive 300-word incident report paragraph analyzing this emergency response.

INCIDENT DATA:
ID: {incident_id} | Location: {address} | Status: {status} | Time: {created_at}

911 CALL: {call_911}
PATROL COMMS: {patrol_comm}
FIRE ENGINE COMMS: {engine_comm}

Write one detailed paragraph covering: what happened, units dispatched, response times, actions taken, communication quality, team coordination effectiveness, and outcome. Focus on performance analysis - what worked well and areas for improvement. Be specific with times and unit names. Use only the data provided."""
    
    summary = llm.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return summary.text

def set_concluded(id: str) -> str:
    """
    Update the incident status to 'CONCLUDED' in the active_incidents collection.
    """
    try:
        result = collection.update_one(
            {"incident_id": id},
            {"$set": {"status": "concluded"}}
        )
        if result.matched_count == 0:
            raise ValueError(f"No incident found with ID: {id}")
        return f"Incident {id} marked as concluded"
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Error updating incident with ID {id}: {e}")


def create_bson(id: str):
    """
    Generate a comprehensive incident report and create a BSON document 
    for the concluded incidents collection with vector embedding.
    Then save it to the knowledge_base collection.
    """
    # Get the original incident from active_incidents
    incident = collection.find_one({"incident_id": id})
    if not incident:
        raise ValueError(f"No incident found with ID: {id}")
    
    # Generate the comprehensive report (may raise ValueError)
    report_text = generate_report(id)
    
    # Generate embedding for vector search
    embedding_result = llm.models.embed_content(
        model="gemini-embedding-001",
        contents=[report_text],
        config=types.EmbedContentConfig(output_dimensionality=768)
    )
    
    # Extract embedding values
    if hasattr(embedding_result.embeddings[0], 'values'):
        embedding = list(embedding_result.embeddings[0].values)
    else:
        embedding = list(embedding_result.embeddings[0])
    
    # Extract location from original incident
    location = incident.get("location", {})
    address_text = location.get("address_text", "Unknown location")
    
    # Get incident_id from original incident
    original_incident_id = incident.get("incident_id", "Unknown")
    
    # Create the BSON document for concluded_incidents collection
    concluded_incident_bson = {
        "original_incident_id": original_incident_id,
        "concluded_at": datetime.utcnow().isoformat() + "Z",
        "location": {
            "address_text": address_text
        },
        "final_summary": report_text,
        "final_summary_embedding": embedding
    }
    
    # Return the BSON document (don't insert yet)
    return concluded_incident_bson

def post_story(id: str):
    """
    Complete workflow: Mark incident as concluded, generate report, create BSON, 
    and save to knowledge_base collection.
    
    Returns the inserted document with its MongoDB _id
    """
    # First, mark incident as concluded (may raise ValueError)
    set_concluded(id)
    
    # Then create the BSON document (may raise ValueError)
    bson_doc = create_bson(id)
    
    # Insert into knowledge_base
    result = knowledge_base.insert_one(bson_doc)
    bson_doc["_id"] = str(result.inserted_id)
    
    return bson_doc


if __name__ == "__main__":
    # Test the function
    # test_id = "690eb0a52e8f17ecb7b23e81"
    test_id = "67"
    
    print("Generating report and creating BSON document...\n")
    result = post_story(test_id)
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print("BSON Document created and saved to knowledge_base successfully!")
        print(f"\nDocument ID: {result.get('_id', 'N/A')}")
        print(f"Original Incident ID: {result['original_incident_id']}")
        print(f"Concluded At: {result['concluded_at']}")
        print(f"Location: {result['location']['address_text']}")
        print(f"Final Summary Length: {len(result['final_summary'])} characters")
        print(f"Embedding Dimensions: {len(result['final_summary_embedding'])}")
        print(f"\nFirst 500 characters of report:\n{result['final_summary'][:500]}...")
