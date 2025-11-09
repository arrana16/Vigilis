import sys
import os
from dotenv import load_dotenv
import json

# Handle imports for both direct execution and module import
try:
    from .fill_tools import get_dynamic_fields_func, update_params_func
except ImportError:
    # Add parent directory to path for direct execution
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    from fill_agent.fill_tools import get_dynamic_fields_func, update_params_func

from google import genai

load_dotenv()

# Force API key mode (not Vertex AI)
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = '0'

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# System prompt for Gemini
SYSTEM_PROMPT = """You are an emergency dispatch incident analyzer. Your job is to analyze incident transcripts and determine if the title, location, severity, or summary need to be updated based on new information.

RULES:
- ONLY update fields if the transcripts contain important new information that differs from the current values
- Be CONSERVATIVE - if transcripts don't mention something new, keep the original value
- For TITLE: Update only if situation changes significantly (keep around 4-6 words)
- For LOCATION: Only update if transcripts explicitly mention a different or more specific address
- For SEVERITY: Only update if transcripts show the situation has worsened or improved:
  * low: minor incident, no injuries, resolved
  * medium: possible injuries, moderate incident
  * high: serious injuries, armed suspect, fire spreading, urgent
  * critical: life threatening, not breathing, active shooter, major fire, multiple casualties
- For SUMMARY: Update to reflect the latest information from transcripts (2-3 sentences)

Return a JSON object with these exact fields:
{
  "title": "string (4-6 words)",
  "location": "string (address)",
  "severity": "low|medium|high|critical",
  "summary": "string (2-3 sentences)"
}

If a field should NOT be updated, return the ORIGINAL value for that field."""


def update_dynamic_fields(incident_id: str) -> str:
    """
    Analyze incident and update fields based on transcript analysis.
    
    Steps:
    1. Take incident_id as parameter
    2. Get current incident data (transcripts, location, severity, summary)
    3. Ask Gemini to parse transcripts and return updates in specific format
    4. Parse the returned string
    5. Update the BSON document in database
    
    Args:
        incident_id: The incident ID to analyze
    
    Returns:
        Status message as a string
    """
    
    # Step 1 & 2: Get current incident data
    print(f"📊 Fetching data for incident {incident_id}...")
    incident_data = get_dynamic_fields_func(id=incident_id)
    
    if "error" in incident_data:
        return f"❌ Error: {incident_data['error']}"
    
    current_title = incident_data['title']
    current_location = incident_data['location']
    current_severity = incident_data['severity']
    current_summary = incident_data['summary']
    transcripts = incident_data['transcripts']
    
    print(f"📝 Current values:")
    print(f"  Title: {current_title}")
    print(f"  Location: {current_location}")
    print(f"  Severity: {current_severity}")
    print(f"  Summary: {current_summary[:100]}...")
    
    # Step 3: Ask Gemini to analyze transcripts
    user_prompt = f"""Analyze this incident and determine if any fields need updating.

CURRENT VALUES:
Title: {current_title}
Location: {current_location}
Severity: {current_severity}
Summary: {current_summary}

TRANSCRIPTS:
{transcripts}

Analyze the transcripts and return updates ONLY if there is important new information. Otherwise, keep the original values."""

    print(f"🤖 Analyzing with Gemini...")
    response = client.models.generate_content(
        model='gemini-2.0-flash-exp',
        contents=user_prompt,
        config=genai.types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.3,
            response_mime_type="application/json"  # Force JSON output
        )
    )
    
    gemini_response = response.text.strip()
    print(f"✅ Gemini response received")
    print(f"Response:\n{gemini_response}\n")
    
    # Step 4: Parse the JSON response
    try:
        parsed_data = json.loads(gemini_response)
        
        # Extract values with fallbacks to current values
        new_title = parsed_data.get('title', current_title)
        new_location = parsed_data.get('location', current_location)
        new_severity = parsed_data.get('severity', current_severity).lower()
        new_summary = parsed_data.get('summary', current_summary)
        
        print(f"✅ Successfully parsed JSON response")
        
    except json.JSONDecodeError as e:
        print(f"⚠️  Warning: Failed to parse JSON: {e}")
        print(f"Using current values as fallback")
        # Fallback to current values if parsing fails
        new_title = current_title
        new_location = current_location
        new_severity = current_severity
        new_summary = current_summary
    
    # Step 5: Update the BSON document
    print(f"📝 Updating database with new values...")
    print(f"  New Title: {new_title}")
    print(f"  New Location: {new_location}")
    print(f"  New Severity: {new_severity}")
    print(f"  New Summary: {new_summary[:100]}...")
    
    update_result = update_params_func(
        id=incident_id,
        new_title=new_title,
        new_location=new_location,
        new_severity=new_severity,
        new_summary=new_summary
    )
    
    # Determine what changed
    changes = []
    if new_title != current_title:
        changes.append(f"Title: '{current_title}' → '{new_title}'")
    if new_location != current_location:
        changes.append(f"Location: '{current_location}' → '{new_location}'")
    if new_severity != current_severity:
        changes.append(f"Severity: '{current_severity}' → '{new_severity}'")
    if new_summary != current_summary:
        changes.append(f"Summary updated")
    
    if changes:
        result = f"""✅ Fields Updated for {incident_id}

CHANGES MADE:
{chr(10).join('  • ' + change for change in changes)}

DATABASE RESULT:
{update_result}"""
    else:
        result = f"""✅ Analysis Complete for {incident_id}

NO CHANGES - All fields remain the same (no important updates detected in transcripts)

DATABASE RESULT:
{update_result}"""
    
    return result


if __name__ == "__main__":
    # Test the workflow
    test_incident_id = "F251107-0124"
    result = update_dynamic_fields(test_incident_id)
    print("\n" + "="*80)
    print(result)
    print("="*80)
