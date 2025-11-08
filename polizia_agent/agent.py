from google.adk.agents.llm_agent import Agent
from tools import update_context_tool

root_agent = Agent(
    model='gemini-2.5-flash',
    name='vigilis_assistant',
    description='An AI assistant for emergency services dispatchers that helps with incident management and provides real-time insights.',
    instruction="""You are Vigilis, an AI assistant for 911 dispatchers and emergency services personnel. 

Your role is to:
- Help dispatchers understand current incidents by retrieving and explaining incident data
- Answer questions about emergency protocols and procedures
- Provide context and insights about ongoing situations
- Assist with incident management decisions

You have access to a tool called 'update_context' that can retrieve incident information from the database. When a user asks about a specific incident, use this tool to get the latest data.

Be professional, concise, and helpful. Your goal is to support emergency services personnel in making fast, informed decisions.""",
    tools=[update_context_tool]
)

def chat(message: str, incident_id: str = None) -> str:
    """
    Send a message to the agent and get a response.
    
    Args:
        message: The user's message/question
        incident_id: Optional incident ID for context
    
    Returns:
        The agent's response as a string
    """
    if incident_id:
        prompt = f"[Current Incident: {incident_id}]\n{message}"
    else:
        prompt = message
    
    response = root_agent.generate(prompt)
    return response