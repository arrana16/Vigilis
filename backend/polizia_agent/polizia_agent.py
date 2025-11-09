from backend.db import update_chat_elements
from .polizia_tools import update_context
from google import genai
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Force API key mode (not Vertex AI)
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = '0'

# Initialize the Gemini client with API key
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# System instruction for the agent
SYSTEM_INSTRUCTION = """You are Vigilis, an AI assistant for 911 dispatchers and emergency services personnel. 

Your role is to:
- Help dispatchers understand current incidents by retrieving and explaining incident data
- Answer questions about emergency protocols and procedures
- Provide context and insights about ongoing situations
- Assist with incident management decisions

You have access to a tool called 'update_context' that can retrieve incident information from the database. When a user asks about a specific incident, use this tool to get the latest data.

Be professional, concise, and helpful. Your goal is to support emergency services personnel in making fast, informed decisions."""

def chat(message: str, incident_id: str = None) -> str:
    """
    Send a message to the agent and get a response.
    
    Args:
        message: The user's message/question
        incident_id: Optional incident ID for context
    
    Returns:
        The agent's response as a string
    """
    message_time = datetime.utcnow().isoformat() + "Z"
    if incident_id:
        prompt = f"[Current Incident: {incident_id}]\n{message}"
    else:
        prompt = message
    
    # Use Gemini with function calling
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=[update_context],
            temperature=0.7
        )
    )
    
    # Handle function calls if needed
    while response.candidates[0].content.parts[0].function_call:
        function_call = response.candidates[0].content.parts[0].function_call
        function_name = function_call.name
        function_args = function_call.args
        
        # Execute the function
        if function_name == 'update_context':
            function_result = update_context(**function_args)
        else:
            function_result = f"Unknown function: {function_name}"
        
        # Send function result back to model
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=[
                prompt,
                response.candidates[0].content,
                genai.types.Content(
                    parts=[genai.types.Part.from_function_response(
                        name=function_name,
                        response={"result": function_result}
                    )]
                )
            ],
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[update_context],
                temperature=0.7
            )
        )

    current_time = datetime.utcnow().isoformat() + "Z"
    elements = [
        {"Author": "Caller", "Content": message, "Time": message_time},
        {"Author": "Polizia", "Content": response.text, "Time": current_time}
    ]

    update_chat_elements(incident_id, elements)
                
    return response.text
