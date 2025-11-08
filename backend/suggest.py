import sys
import os
from dotenv import load_dotenv
from bson import ObjectId

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

def summarize_current_status(id: str) -> str: 
    try:
        incident = collection.find_one({"_id": ObjectId(id)})
    except Exception as e:
        raise ValueError(f"Error querying incident with ID {id}: {e}")
    
    if not incident:
        raise ValueError(f"No incident found with ID: {id}")
    
    transcripts = incident.get("transcripts", {})
    
    transcript_text = ""
    for key, value in transcripts.items():
        if value:
            transcript_text += f"\n{key}:\n{value}\n"
    
    if not transcript_text.strip():
        raise ValueError("No transcript data available for this incident.")
    
    prompt = f"""Based on the following emergency incident transcripts, provide a concise summary of the current status: 
            {transcript_text} Summary:"""
    
    summary = llm.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return summary

def vectorize_running_summary(text) -> list:
    result = llm.models.embed_content(
        model = "gemini-embedding-001",
        contents = [text],
        config=types.EmbedContentConfig(output_dimensionality=768)
    )
    # Extract the actual embedding values from the ContentEmbedding object
    if hasattr(result.embeddings[0], 'values'):
        return result.embeddings[0].values
    return result.embeddings[0] 

def retrieve_similar_stories(vector) -> list:
    """
    Retrieve 2 similar concluded incidents from the vector database 
    based on semantic similarity to the current incident summary.
    """
    pipeline = [
        {
            "$vectorSearch": {
                "queryVector": list(vector),
                "path": "final_summary_embedding",
                "numCandidates": 10,
                "limit": 2,
                "index": "vector_index"
            }
        },
        {
            "$project": {
                "original_incident_id": 1,
                "location": 1,
                "outcome_type": 1,
                "final_summary": 1,
                "concluded_at": 1,
                "score": { "$meta": "vectorSearchScore" }
            }
        }
    ]
    results = knowledge_base.aggregate(pipeline)
    similar_stories = []
    
    for doc in results:
        similar_stories.append({
            "incident_id": doc.get("original_incident_id", "Unknown"),
            "location": doc.get("location", {}).get("address_text", "Unknown location"),
            "outcome_type": doc.get("outcome_type", "Unknown outcome"),
            "summary": doc.get("final_summary", "No summary available"),
            "concluded_at": doc.get("concluded_at", "Unknown date"),
            "similarity_score": doc.get("score", 0)
        })
    
    return similar_stories

def givesuggestions(eventid: str) -> str:
    # This will raise ValueError if incident not found - let it propagate
    text = summarize_current_status(eventid)
    vector = vectorize_running_summary(text)
    similar_stories = retrieve_similar_stories(vector)
    
    prompt = f"""You are an expert AI assistant for 911 dispatchers with access to a database of past incident outcomes. Your purpose is to help dispatchers make data-driven decisions by learning from what worked and what didn't in similar situations.

ROLE: You are an experienced emergency response analyst who has reviewed thousands of incident outcomes. You identify patterns in successful responses and flag approaches that led to complications.

CONTEXT: You have two data sources:
1. CURRENT SITUATION: The live incident unfolding right now
2. HISTORICAL DATA: Similar past incidents with their complete outcomes, response details, and what happened

CRITICAL TASK: Analyze the historical data to extract SPECIFIC lessons:
- What actions led to SUCCESSFUL outcomes in similar situations?
- What mistakes or missed opportunities occurred that should be AVOIDED?
- What unexpected complications arose that responders should anticipate?
- What resources or tactics proved most effective?

RULES:
1. LEARN FROM SUCCESS: If a similar incident was resolved well, identify the SPECIFIC actions that contributed (e.g., "Past incident shows that calling for K-9 backup within first 5 minutes reduced search time by 40%")

2. LEARN FROM FAILURE: If a similar incident had complications, explicitly warn about them (e.g., "WARNING: In 2 similar cases, delays in medical dispatch led to worse outcomes - recommend immediate EMT staging")

3. IDENTIFY PATTERNS: Look for recurring themes across similar incidents (e.g., "All 3 similar domestic calls at this address escalated when only 1 unit responded - recommend 2-unit dispatch")

4. BE SPECIFIC WITH DATA: Reference the historical outcomes directly (e.g., "Similar incident #X resolved in 12 minutes when supervisor arrived early vs. 45 minutes without supervisor")

5. ACTIONABLE + EVIDENCE-BASED: Every suggestion must cite WHY based on historical data (e.g., "Dispatch traffic control [BECAUSE: Past incident at this intersection had 2 secondary accidents due to rubbernecking]")

6. HIGHLIGHT UNIQUE INSIGHTS: Focus on non-obvious patterns that only emerge from analyzing past data (not generic best practices)

OUTPUT FORMAT: Provide 3-5 numbered suggestions. Each suggestion should have:
- The ACTION to take
- The REASON based on historical data (what worked/didn't work before)

Example format:
1. [ACTION] - Historical insight: [What happened in similar past incidents and why this matters]
2. [ACTION] - Historical insight: [Pattern observed across multiple incidents]

CURRENT SITUATION:
{text}

HISTORICAL DATA FROM SIMILAR PAST INCIDENTS:
{similar_stories}

Analyze the historical outcomes and provide data-driven suggestions:"""

    response = llm.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text

if __name__ == "__main__":
    id = "67"
    # id = "690eb0a52e8f17ecb7b23e81"
    suggestions = givesuggestions(id)
    print("Suggestions:")
    print(suggestions)