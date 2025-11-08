from google.adk.agents.llm_agent import Agent
from tools import update_context_tool

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction='Answer user questions to the best of your knowledge',
    tools=[update_context_tool]
)