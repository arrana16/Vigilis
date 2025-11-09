import os
import pymongo
from google import genai
from google.genai import types
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# --- 1. Configuration & Setup ---

# Get credentials from environment variables
MONGO_PASSWORD = os.environ.get("MONGO_PASSWORD")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not MONGO_PASSWORD or not GEMINI_API_KEY:
    raise EnvironmentError(
        "Please set MONGO_PASSWORD and GEMINI_API_KEY environment variables in .env file."
    )

# Build MongoDB URI
MONGO_URI = f"mongodb+srv://cyrus:{MONGO_PASSWORD}@cluster0.rznqb.mongodb.net/?appName=Cluster0"

# Configure the Google Gemini client
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# Initialize the MongoDB client
try:
    client = pymongo.MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)
    DB = client["dispatch_db"]
    client.admin.command('ping')
    print("Successfully connected to MongoDB Atlas!")
except pymongo.errors.ConnectionFailure as e:
    print(f"Error connecting to MongoDB: {e}")
    exit(1)

# --- 2. Embedding Function ---

def embed_document(text: str) -> list[float]:
    """
    Generates an embedding for a **storage document**
    using the Google Gemini embedding model.
    """
    try:
        result = gemini_client.models.embed_content(
            model="models/text-embedding-004",
            contents=text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT"
            )
        )
        # Extract the embedding values from the result
        return result.embeddings[0].values
    except Exception as e:
        print(f"Error generating document embedding: {e}")
        return []

# --- 3. Fake Incident Data ---

# A list of fake summaries and their outcomes
FAKE_INCIDENTS = [
    {
        "original_incident_id": "F250110-0080",
        "location_text": "789 Pine St, Atlanta, GA",
        "outcome_type": "False Alarm (HVAC)",
        "final_summary": "Initial 911 call reported smoke from the roof of the 789 Pine St commercial building. Patrol and Engine units responded. Officer on scene (PatP_22) reported light grey smoke from a rooftop vent. Building manager confirmed a scheduled test of the HVAC system was underway. All units cleared, false alarm."
    },
    {
        "original_incident_id": "F250215-0130",
        "location_text": "456 Oak Ave, Atlanta, GA",
        "outcome_type": "Minor Electrical Fire",
        "final_summary": "Caller reported seeing flames from the garage of 456 Oak Ave. Officer (Pat_12) arrived and confirmed smoke but no visible flames from outside. Advised a strong smell of burning plastic / electrical. Fire units entered and found a small, smoldering electrical fire in the garage wall, which was extinguished. No injuries. Cause was faulty wiring."
    },
    {
        "original_incident_id": "F250301-0025",
        "location_text": "1000 Peachtree St, Atlanta, GA",
        "outcome_type": "Domestic Dispute",
        "final_summary": "Multiple 911 calls reported a loud argument and sounds of breaking glass from apartment 3B, 1000 Peachtree. Officers responded to a possible domestic violence situation. On scene, officers (Pat_05, Pat_07) made contact with two individuals. The situation was de-escalated and one party left voluntarily. No arrests."
    },
    {
        "original_incident_id": "F250420-0500",
        "location_text": "Piedmont Park, Atlanta, GA",
        "outcome_type": "Suspicious Person",
        "final_summary": "Caller reported a person acting erratically near the park entrance, possibly concealing a weapon. Officers (Pat_19, Pat_20) responded and made contact. The individual was found to be in mental distress but unarmed. Officers requested an ambulance for a mental health evaluation. Situation resolved peacefully."
    }
]

# --- 4. Main Seeding Function ---

def seed_database():
    """
    Generates and inserts the fake documents into the
    `incident_knowledge_base` collection.
    """
    collection = DB["incident_knowledge_base"]
    
    # Optional: Clear the collection first to avoid duplicates
    print(f"Clearing old documents from '{collection.name}'...")
    collection.delete_many({})
    
    print(f"Generating and inserting {len(FAKE_INCIDENTS)} new documents...")
    
    docs_to_insert = []
    for incident in FAKE_INCIDENTS:
        # 1. Get the summary text
        summary_text = incident["final_summary"]
        
        # 2. Generate the embedding
        embedding = embed_document(summary_text)
        
        if not embedding:
            print(f"Skipping incident {incident['original_incident_id']} due to embedding error.")
            continue
            
        # 3. Build the final document
        new_doc = {
            "original_incident_id": incident["original_incident_id"],
            "concluded_at": datetime.now(timezone.utc).isoformat(),
            "location": {"address_text": incident["location_text"]},
            "outcome_type": incident["outcome_type"],
            "final_summary": summary_text,
            "final_summary_embedding": embedding  # Add the vector
        }
        docs_to_insert.append(new_doc)

    # 4. Insert all documents in one batch
    if docs_to_insert:
        result = collection.insert_many(docs_to_insert)
        print(f"Successfully inserted {len(result.inserted_ids)} documents.")
    else:
        print("No documents were inserted.")

if __name__ == "__main__":
    print("Starting database seeding process...")
    seed_database()
    print("Database seeding complete.")