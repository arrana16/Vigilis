import sys
import os
from dotenv import load_dotenv
import json
import requests

# Handle imports for both direct execution and module import
try:
    from .fill_tools import get_dynamic_fields_func, update_params_func
except ImportError:
    # Add parent directory to path for direct execution
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    from fill_agent.fill_tools import get_dynamic_fields_func, update_params_func

from google import genai
import time

load_dotenv()

# Force API key mode (not Vertex AI)
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = '0'

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# CRITICAL: Rate limiting to prevent infinite loops from MongoDB triggers
_last_update_time = {}
_UPDATE_COOLDOWN_SECONDS = 20  # Minimum 60 seconds between updates for same incident

# System prompt for Gemini
SYSTEM_PROMPT = """You are an emergency dispatch incident analyzer. Your job is to analyze incident transcripts and determine if the title, location, severity, or summary need to be updated based on new information.

RULES:
- ONLY update fields if the transcripts contain important new information that differs from the current values
- if transcripts don't mention new information, keep the original value
- For TITLE: Update based on changes in the transcripts
- For LOCATION: Extract an address string from the transcripts. KEEP STRICT ADDRESS FORMATTING. eg("123 Main St, Springfield, IL 62701" or "Central Park, New York, NY")
- For SEVERITY: Only update if transcripts show the situation has worsened or improved:
  * low: minor incident, no injuries, resolved
  * medium: possible injuries, moderate incident
  * high: serious injuries, armed suspect, fire spreading, urgent
  * critical: life threatening, not breathing, active shooter, major fire, multiple casualties
- For SUMMARY: Update to reflect the latest information from transcripts (2-3 sentences)

Return a JSON object with these exact fields:
{
  "title": "string (4-6 words)",
  "location": "string (full descriptive address or place name)",
  "severity": "low|medium|high|critical",
  "summary": "string (2-3 sentences)"
}

If a field should NOT be updated, return the ORIGINAL value for that field."""


def geocode_address(address: str) -> dict:
    """
    Convert an address string to longitude/latitude coordinates using Nominatim (OpenStreetMap).
    Preprocesses address by removing prepositions like "in", "at", "near" for better results.
    
    Args:
        address: The address string to geocode
    
    Returns:
        Dictionary with 'longitude', 'latitude', and 'formatted_address'
        Returns None values if geocoding fails
    """
    if not address or address.strip() == "":
        print(f"⚠️  Empty address provided for geocoding.")
        return {"longitude": None, "latitude": None, "formatted_address": address}
    
    def try_geocode(query: str) -> dict:
        """Helper function to attempt geocoding"""
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": query,
                "format": "json",
                "limit": 1
            }
            headers = {
                "User-Agent": "Vigilis-Emergency-Dispatch/1.0"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0:
                result = data[0]
                return {
                    "longitude": float(result["lon"]),
                    "latitude": float(result["lat"]),
                    "formatted_address": result.get("display_name", query)
                }
            return None
        except Exception as e:
            print(f"   ⚠️  Geocoding exception: {e}")
            return None
    
    # PREPROCESS: Extract location after prepositions "in", "at", "near", "on"
    # e.g., "Mercedes-Benz Stadium in Atlanta, Georgia" → "Atlanta, Georgia"
    # e.g., "Building at Georgia Tech" → "Georgia Tech"
    processed_address = address
    prepositions = [" in ", " at ", " near ", " on "]
    
    for prep in prepositions:
        if prep in address.lower():
            # Extract everything after the preposition
            parts = address.split(prep, 1)
            if len(parts) == 2:
                extracted = parts[1].strip()
                print(f"   📍 Extracted location after '{prep.strip()}': {extracted}")
                
                # Try geocoding the extracted part first
                result = try_geocode(extracted)
                if result:
                    result["formatted_address"] = address  # Keep original
                    return result
                
                # If that fails, also try the full original address
                processed_address = extracted
                break
    
    # Try original/processed address
    print(f"   🌍 Geocoding: {processed_address}")
    result = try_geocode(processed_address)
    if result:
        result["formatted_address"] = address  # Keep original description
        return result
    
    # Fallback: Try comma-separated parts (city, state)
    if "," in processed_address:
        parts = [p.strip() for p in processed_address.split(",")]
        if len(parts) >= 2:
            general_location = ", ".join(parts[-2:])  # Last 2 parts
            print(f"   🔄 Trying city/state fallback: {general_location}")
            result = try_geocode(general_location)
            if result:
                result["formatted_address"] = address
                return result
    
    print(f"⚠️  No geocoding results found for: {address}")
    return {"longitude": None, "latitude": None, "formatted_address": address}
    print(f"⚠️  No geocoding results found for: {address}")
    return {"longitude": None, "latitude": None, "formatted_address": address}


def update_dynamic_fields(incident_id: str) -> str:
    """
    Analyze incident and update fields based on transcript analysis.
    Includes rate limiting to prevent infinite loops from MongoDB triggers.
    
    Steps:
    1. Check rate limit (prevent updates within cooldown period)
    2. Get current incident data (transcripts, location, severity, summary)
    3. Ask Gemini to parse transcripts and return updates in specific format
    4. Parse the returned string
    5. Update the BSON document in database
    
    Args:
        incident_id: The incident ID to analyze
    
    Returns:
        Status message as a string
    """
    
    # CRITICAL: Rate limiting to prevent infinite loops from MongoDB triggers
    current_time = time.time()
    last_update = _last_update_time.get(incident_id, 0)
    time_since_last = current_time - last_update
    
    if time_since_last < _UPDATE_COOLDOWN_SECONDS:
        remaining = int(_UPDATE_COOLDOWN_SECONDS - time_since_last)
        print(f"⏳ RATE LIMITED: Skipping update for {incident_id} (cooldown: {remaining}s remaining)")
        return f"⏳ Rate limited: Update skipped (cooldown: {remaining}s remaining)"
    
    # Update the last update timestamp
    _last_update_time[incident_id] = current_time
    print(f"✅ Rate limit check passed for {incident_id}")
    
    # Step 1 & 2: Get current incident data
    print(f"📊 Fetching data for incident {incident_id}...")
    incident_data = get_dynamic_fields_func(id=incident_id)
    
    if "error" in incident_data:
        return f"❌ Error: {incident_data['error']}"
    
    current_title = incident_data['title']
    current_location = incident_data['location']
    current_severity = incident_data['severity']
    current_summary = incident_data['summary']
    current_coordinates = incident_data.get('coordinates', [])
    transcripts = incident_data['transcripts']
    
    print(f"📝 Current values:")
    print(f"  Title: {current_title}")
    print(f"  Location: {current_location}")
    print(f"  Coordinates: {current_coordinates if current_coordinates else 'Not set'}")
    print(f"  Severity: {current_severity}")
    print(f"  Summary: {current_summary[:100]}...")
    
    # Step 3: Ask Gemini to analyze transcripts
    user_prompt = f"""Analyze this incident and determine if any fields need updating based on transcripts EMPTY FIELDS MEANS IMMEDIATE UPDATE REQUIRED.

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
    
    # Step 5: Geocode the location if it changed OR if coordinates are missing
    coordinates = None
    needs_geocoding = False
    
    # Check if location changed
    if new_location and new_location != current_location:
        needs_geocoding = True
        print(f"🗺️  Location changed, geocoding: {new_location}")
    # Check if coordinates are missing but we have a location
    elif new_location and (not current_coordinates or len(current_coordinates) == 0):
        needs_geocoding = True
        print(f"🗺️  Coordinates missing, geocoding existing location: {new_location}")
    else:
        print(f"ℹ️  Location unchanged and coordinates exist: {current_coordinates}")
    
    if needs_geocoding:
        geo_result = geocode_address(new_location)
        
        if geo_result["longitude"] is not None and geo_result["latitude"] is not None:
            coordinates = [geo_result["longitude"], geo_result["latitude"]]
            print(f"✅ Geocoded: [{geo_result['longitude']}, {geo_result['latitude']}]")
            # Keep original address text (don't overwrite with formatted version)
        else:
            print(f"⚠️  Could not geocode location, using text only")
    
    # Step 6: Update the BSON document
    print(f"📝 Updating database with new values...")
    print(f"  New Title: {new_title}")
    print(f"  New Location: {new_location}")
    if coordinates:
        print(f"  New Coordinates: {coordinates}")
    print(f"  New Severity: {new_severity}")
    print(f"  New Summary: {new_summary[:100]}...")
    
    update_result = update_params_func(
        id=incident_id,
        new_title=new_title,
        new_location=new_location,
        new_severity=new_severity,
        new_summary=new_summary,
        coordinates=coordinates
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
    test_incident_id = "17bc8fd7-085f-4063-89ed-826aaded3fd2"
    result = update_dynamic_fields(test_incident_id)
    print("\n" + "="*80)
    print(result)
    print("="*80)


