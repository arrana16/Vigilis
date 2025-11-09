from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

print(os.getenv("GEMINI_API_KEY"))


client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

result = client.models.embed_content(
    model="gemini-embedding-001",
    contents="Initial 911 call reported smoke from the roof of the 789 Pine St commercial building. Patrol and Engine units responded. Officer on scene (PatP_22) reported light grey smoke from a rooftop vent. Building manager confirmed a scheduled test of the HVAC system was underway. All units cleared, false alarm.",
    config=types.EmbedContentConfig(output_dimensionality=768)
)

[embedding_obj] = result.embeddings
embedding_length = len(embedding_obj.values)

print(embedding_obj.values)