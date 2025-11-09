import sys
import os
from dotenv import load_dotenv
from bson import ObjectId
from model_config import GEMINI_MODEL

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
        incident = collection.find_one({"incident_id": id})
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
    
    prompt = f"""Based on the following emergency incident transcripts, provide a concise summary of the current status. 
    
You will be given transcript data from an emergency incident. Parse this information and provide a very clear summary of what is currently happening.

Transcripts:
{transcript_text}

Provide only the summary text, no additional formatting:"""
    
    summary = llm.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    # Extract text from response object
    return summary.text

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

def retrieve_similar_stories(vector, similarity_threshold: float = 0.7) -> list:
    """
    Retrieve 2 similar concluded incidents from the vector database 
    based on semantic similarity to the current incident summary.
    Only returns incidents with similarity score above the threshold.
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
        score = doc.get("score", 0)
        # Only include results above similarity threshold
        if score >= similarity_threshold:
            similar_stories.append({
                "original_incident_id": doc.get("original_incident_id", "Unknown"),
                "location": doc.get("location", {}).get("address_text", "Unknown location"),
                "final_summary": doc.get("final_summary", "No summary available"),
                "concluded_at": doc.get("concluded_at", "Unknown date"),
                "similarity_score": score
            })
    
    return similar_stories

def givesuggestions(eventid: str) -> str:
    # This will raise ValueError if incident not found - let it propagate
    text = summarize_current_status(eventid)
    vector = vectorize_running_summary(text)
    similar_stories = retrieve_similar_stories(vector)
    
    # If no similar stories meet the threshold, provide general guidance
    if not similar_stories:
        return "No sufficiently similar past incidents found. Proceed with standard protocols and request supervisor guidance if needed."
    
    prompt = f"""You are an AI assistant providing data-driven suggestions for 911 dispatchers based on historical incident outcomes.

CRITICAL REQUIREMENTS:
1. Each ACTION must be 8-12 words - concise and actionable
2. Each Historical insight must be 7-10 words - dense with data
3. Extract IDEAS and PATTERNS from past incidents - DO NOT mention incident IDs or reference specific case numbers
4. Use EXACT formatting with **ACTION:** and **Historical insight:** labels
5. Focus only on the most impactful actions

YOUR TASK:
Analyze the historical data from similar past incidents. Extract ONLY the most critical IDEAS and PATTERNS that apply to the current situation.

- What approaches or tactics led to SUCCESS in similar situations?
- What strategies or decisions should be AVOIDED based on past failures?
- What general patterns emerged that are relevant now?

IMPORTANT: Reference IDEAS and PATTERNS only (e.g., "early backup reduced response times", "delaying medical support worsened outcomes"). 
DO NOT mention incident IDs, case numbers, or specific incident references.

CURRENT SITUATION:
{text}

HISTORICAL DATA FROM SIMILAR PAST INCIDENTS:
{similar_stories}

OUTPUT FORMAT:
Provide 3-5 suggestions. Each suggestion MUST follow this EXACT format:
**ACTION:** [8-12 word actionable directive]
**Historical insight:** [7-10 word pattern or idea from past incidents]

Example format:
**ACTION:** Dispatch two units immediately instead of one for domestic calls
**Historical insight:** Multiple responders prevented escalation in similar volatile situations

**ACTION:** Request K-9 backup within first five minutes of search operations
**Historical insight:** Early specialized backup significantly reduced search duration times

Generate suggestions now (reference ideas/patterns only, NO incident IDs):"""

    response = llm.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    return response.text

if __name__ == "__main__":
    id = "af9a64a1-c6d0-4aca-818b-09a2ad4fa4f2"
    # id = "690eb0a52e8f17ecb7b23e81"
    suggestions = givesuggestions(id)
    print("Suggestions:")
    print(suggestions)