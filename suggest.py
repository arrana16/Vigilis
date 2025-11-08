import sys
import os
from dotenv import load_dotenv
from bson import ObjectId

# Load environment variables from .env file
load_dotenv()

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
        return f"Error querying incident with ID {id}: {e}"
    
    if not incident:
        return f"No incident found with ID: {id}"
    
    transcripts = incident.get("transcripts", {})
    
    transcript_text = ""
    for key, value in transcripts.items():
        if value:
            transcript_text += f"\n{key}:\n{value}\n"
    
    if not transcript_text.strip():
        return "No transcript data available for this incident."
    
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
    text = summarize_current_status(eventid)
    vector = vectorize_running_summary(text)
    similar_stories = retrieve_similar_stories(vector)
    
    prompt = f"""You are an expert AI assistant for 911 dispatchers. Your sole purpose is to help a human dispatcher make faster, safer, and more informed decisions by providing actionable suggestions.

ROLE: Your role is to act as an experienced partner who can see patterns and potential risks that a busy dispatcher might miss. You are calm, precise, and proactive.

CONTEXT: You will be provided with two pieces of information:
1. CURRENT SITUATION: The most up-to-date summary of the live, active incident.
2. SIMILAR PAST INCIDENTS: A list of summaries and outcomes from concluded events that are relevant to the current situation. This is your "memory" or "experience."

TASK: Your primary task is to analyze the CURRENT SITUATION in light of the SIMILAR PAST INCIDENTS and generate a short list of concise, actionable suggestions for the dispatcher.

RULES:
1. ACTIONABLE: Every suggestion must be a clear action the dispatcher can take (e.g., "Ask Officer Smith to check the rear entrance," "Recommend dispatching a K-9 unit," "Query the caller about any unusual sounds").
2. CONCISE: Suggestions must be short and easy to read. No long paragraphs.
3. DO NOT BE OBVIOUS: Do not suggest things that have clearly already happened (e.g., if an officer is on scene, do not suggest "Dispatch an officer").
4. USE THE RAG CONTEXT: If the past incidents show a common, non-obvious outcome (e.g., "Note: Three past 'smoke' calls at this location were due to a faulty HVAC unit"), your suggestion should reflect this (e.g., "Ask officer to check for a building HVAC malfunction").
5. PRIORITIZE SAFETY: If the context implies a potential risk to officers or civilians, your suggestions should prioritize mitigating that risk.
6. BE NEW: Your goal is to provide new insights, not just repeat what's in the summary.

OUTPUT FORMAT: Provide a numbered list of 3-5 actionable suggestions.

CURRENT SITUATION:
{text}

SIMILAR PAST INCIDENTS:
{similar_stories}

Provide your suggestions:"""

    response = llm.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text

if __name__ == "__main__":
    id = "690eb0a52e8f17ecb7b23e81"
    suggestions = givesuggestions(id)
    print("Suggestions:")
    print(suggestions)