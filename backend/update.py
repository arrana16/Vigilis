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
        incident = collection.find_one({"_id": ObjectId(id)})
    except Exception as e:
        return f"Error querying incident with ID {id}: {e}"
    
    if not incident:
        return f"No incident found with ID: {id}"
    
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
    
    prompt = f"""You are a professional emergency services documentation specialist and performance analyst. Your task is to create a comprehensive incident report that not only documents what happened, but also analyzes the team's response effectiveness.

CRITICAL INSTRUCTIONS:
- Carefully analyze ALL transcript data provided
- Evaluate response times, communication quality, and coordination
- Identify what the team did well and any areas for improvement
- Extract specific details about unit performance and decision-making
- Note the sequence of events and how quickly actions were taken

INCIDENT DATA:
- Incident ID: {incident_id}
- Location: {address}
- Coordinates: {coords}
- Date/Time: {created_at}
- Status: {status}
- Current Summary: {current_summary}

911 CALL TRANSCRIPT: 
{call_911}

PATROL COMMUNICATIONS: 
{patrol_comm}

FIRE ENGINE COMMUNICATIONS: 
{engine_comm}

Generate a professional incident report of approximately 300 words that includes:

1. INCIDENT OVERVIEW 
   - Report #, Date/Time, Location, Type of emergency

2. SITUATION SUMMARY 
   - What was reported and by whom
   - Initial assessment and severity
   - Key details from the 911 call

3. RESPONSE ANALYSIS & TIMELINE
   - Which units were dispatched and when
   - Response times and arrival times
   - Actions taken by each unit
   - Quality of communication between dispatcher and units
   - Coordination effectiveness between different responding teams

4. PERFORMANCE EVALUATION
   - What the team did effectively
   - Response time assessment
   - Communication clarity and professionalism
   - Any delays or issues encountered
   - Suggestions for improvement if applicable

5. CURRENT STATUS & OUTCOME
   - Current state of the incident
   - Outstanding actions or follow-up needed

IMPORTANT: Base your analysis ONLY on the transcript data provided. Be specific about times, unit names, and actions. Evaluate the response objectively and professionally. Use formal language appropriate for official emergency services documentation."""
    
    summary = llm.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
    )

    return summary.text

def set_concluded(id: str):
    """
    Update the incident status to 'CONCLUDED' in the active_incidents collection.
    """
    try:
        result = collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"status": "concluded"}}
        )
        if result.matched_count == 0:
            return f"No incident found with ID: {id}"
        return f"Incident with ID {id} marked as CONCLUDED."
    except Exception as e:
        return f"Error updating incident with ID {id}: {e}"


def create_bson(id: str):
    """
    Generate a comprehensive incident report and create a BSON document 
    for the concluded incidents collection with vector embedding.
    Then save it to the knowledge_base collection.
    """
    try:
        # Get the original incident from active_incidents
        incident = collection.find_one({"_id": ObjectId(id)})
        if not incident:
            return {"error": f"No incident found with ID: {id}"}
        
        # Generate the comprehensive report
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
        
        # Insert the document into the knowledge_base collection
        insert_result = knowledge_base.insert_one(concluded_incident_bson)
        concluded_incident_bson["_id"] = str(insert_result.inserted_id)
        
        return concluded_incident_bson
        
    except Exception as e:
        return {"error": f"Error creating BSON document: {str(e)}"}


if __name__ == "__main__":
    # Test the function
    test_id = "690eb0a52e8f17ecb7b23e81"
    
    print("Generating report and creating BSON document...\n")
    set_concluded(test_id)
    result = create_bson(test_id)
    
    
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
