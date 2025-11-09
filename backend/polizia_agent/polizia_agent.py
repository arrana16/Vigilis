
from .polizia_tools import get_incident_context
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
import google.generativeai as genai
import os
from dotenv import load_dotenv
from db import update_chat_elements


load_dotenv()


# System instruction for the Vigilis agent
SYSTEM_INSTRUCTION = """You are Vigilis, an AI assistant for 911 dispatchers and emergency services personnel.

Your role is to:
- Answer questions about active incidents by retrieving real-time data from the database
- Help dispatchers understand incident locations, status, and details
- Explain transcripts from 911 calls and radio communications
- Provide context and insights about ongoing emergency situations
- Assist with incident management decisions

IMPORTANT: When a user asks about ANY detail of an incident (location, status, summary, transcripts, etc.),
you MUST call the 'get_incident_context' tool to retrieve the current incident data from the database.

Examples of when to call the tool:
- "Where is the fire?" → Call tool to get location
- "What's the incident summary?" → Call tool to get current_summary
- "What did the 911 caller say?" → Call tool to get transcripts 
- "What's happening?" → Call tool to get all details
- "What's the status?" → Call tool to get status field

After retrieving the data from the tool, extract the relevant information and provide a clear,
concise answer focusing on what the dispatcher needs to know.

Be professional, accurate, and helpful. Your goal is to support emergency services personnel
in making fast, informed decisions during critical situations."""


# Create the Vigilis agent using Google ADK
vigilis_agent = LlmAgent(
    name="VIGILISAgent",
    description="AI assistant for 911 dispatchers that retrieves and explains incident data",
    model="gemini-2.0-flash-exp",  # Using Gemini 2.0 Flash
    instruction=SYSTEM_INSTRUCTION,
    tools=[FunctionTool(get_incident_context)]  # Wrap the function in FunctionTool
)


# Configure Gemini with API key (using google.generativeai for API key support)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def chat(message: str, incident_id: str = None) -> str:
    """
    Send a message to the Vigilis agent and get a response.
    
    This function uses Google ADK's function tool definition with direct Gemini API calls
    to provide function calling capabilities while maintaining simplicity.
    
    Args:
        message: The user's message/question
        incident_id: Optional incident ID for context
    
    Returns:
        The agent's response as a string
    """
    # Prepare the prompt with incident context if provided
    if incident_id:
        prompt = f"[Current Incident ID: {incident_id}]\n\nUser question: {message}"
    else:
        prompt = message
    
    print(f"\n🔵 VIGILIS Agent processing: {message}")
    if incident_id:
        print(f"   Incident ID: {incident_id}")
    
    # Define the tool for Gemini function calling
    tool_config = {
        "function_declarations": [{
            "name": "get_incident_context",
            "description": get_incident_context.__doc__ or "Retrieve detailed incident information from the database",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {
                        "type": "string",
                        "description": "The ID of the incident to retrieve (e.g., 'INC-001' or UUID format)"
                    }
                },
                "required": ["incident_id"]
            }
        }]
    }
    
    # Create the model with tools
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-exp",
        system_instruction=SYSTEM_INSTRUCTION,
        tools=[tool_config]
    )
    
    # Start a chat session for easier multi-turn conversation
    chat_session = model.start_chat()
    
    # Send initial request to Gemini with tools
    response = chat_session.send_message(prompt)
    
    # Check if the model wants to call a function
    if response.candidates[0].content.parts and hasattr(response.candidates[0].content.parts[0], 'function_call'):
        function_call = response.candidates[0].content.parts[0].function_call
        
        print(f"   🔧 Calling tool: {function_call.name}(incident_id={function_call.args['incident_id']})")
        
        # Execute the function
        function_result = get_incident_context(function_call.args['incident_id'])
        
        # Send the function result back to the model using chat session
        response = chat_session.send_message(
            genai.protos.Content(
                parts=[genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=function_call.name,
                        response={"result": function_result}
                    )
                )]
            )
        )
    
    # Extract the final text response
    response_text = response.text if hasattr(response, 'text') else ""
    
    if not response_text:
        response_text = "No response generated"
    
    print(f"✅ VIGILIS Agent responded ({len(response_text)} chars)\n")
    
    # Store in chat elements
    chat_entry = {"Dispatcher Response": response_text, "Agent": response_text}
    update_chat_elements(incident_id, chat_entry)
    
    # Return the response text
    return response_text
