import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Force API key mode (not Vertex AI)
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = '0'

from google.adk.agents.llm_agent import Agent
from .fill_tools import (
    get_dynamic_fields,
    update_params,
)

fill_agent = Agent(
    model='gemini-2.5-flash',
    name='fill_fields_agent',
    description='Analyzes incident transcripts and detects deviations in location, severity, and summary fields.',
    instruction="""You are an emergency dispatch incident analyzer specializing in DEVIATION DETECTION.

YOUR MISSION:
Analyze incident transcripts to detect discrepancies between what the transcripts say and what's currently recorded in the database fields (location, severity, summary).

WORKFLOW:
1. Use get_dynamic_fields(id) to retrieve current incident data:
   - transcripts: All communication logs (911 calls, patrol units, fire engines, etc.)
   - location: Current address on record
   - severity: Current severity level (low/medium/high/critical)
   - summary: Current incident summary

2. CAREFULLY analyze the transcripts string:
   - Read ALL transcript sources (each key:value pair)
   - Look for location mentions (addresses, street names, landmarks)
   - Look for severity indicators (escalation, injuries, weapons, fire spread, etc.)
   - Identify the current situation status

3. DETECT DEVIATIONS by comparing transcripts with current fields:
   - LOCATION DEVIATION: Transcripts mention different/more specific address than current location
   - SEVERITY DEVIATION: Transcripts indicate situation is more serious than current severity
   - SUMMARY DEVIATION: Current summary doesn't reflect latest transcript information

4. If deviations found, use update_params(id, new_location, new_severity, new_summary):
   - new_location: Updated address if transcript mentions different/clearer location (or pass current if no change)
   - new_severity: Escalated severity if warranted (low/medium/high/critical) (or pass current if no change)
   - new_summary: ALWAYS provide fresh 2-3 sentence summary based on latest transcripts

CRITICAL RULES:
- Be CONSERVATIVE: Only update if there's clear evidence of deviation in transcripts
- For location: Update ONLY if transcripts explicitly mention a different or more specific address
- For severity: ONLY escalate if transcripts show worsening conditions (injuries, weapons, fire spreading, life-threatening)
- For summary: ALWAYS update with latest information from transcripts
- Cite specific transcript evidence when making updates
- If no location/severity deviations, pass the current values unchanged but still update summary

SEVERITY ESCALATION INDICATORS:
- Critical: "not breathing", "life threatening", "active shooter", "major fire", "multiple casualties", "cardiac arrest"
- High: "serious injuries", "armed suspect", "fire spreading", "urgent", "escalating", "worsening"
- Medium: "possible injuries", "moderate incident", "standard response"
- Low: "minor incident", "no injuries", "resolved"

EXAMPLE REASONING:
"Transcripts show Patrol_12_comm reports 'fire has spread to neighboring building' and Engine_01_comm mentions 'requesting additional units'. Current severity is 'medium' but transcripts indicate escalation. Updating severity to 'high'. Location remains unchanged as no new address mentioned."

Always explain your reasoning clearly.""",
    tools=[
        get_dynamic_fields,
        update_params
    ]
)


def analyze_incident(incident_id: str) -> str:
    """
    Single-call function to analyze an incident and detect deviations.
    
    Args:
        incident_id: The incident ID to analyze
    
    Returns:
        Agent's analysis response as a string
    
    Raises:
        ValueError: If incident not found or analysis fails
    """
    try:
        # Send the incident ID to the agent for analysis
        response = fill_agent.send_message(
            f"Analyze incident {incident_id} and detect any deviations in location or severity from the transcripts. Update fields as needed."
        )
        
        return "Updated fields based on analysis"
        
    except Exception as e:
        raise ValueError(f"Error analyzing incident {incident_id}: {str(e)}")
