from langchain.agents import initialize_agent
from langchain.agents import Tool
from langchain.agents import AgentType
from tools import (get_surroundings_description,
                    places_nearby)
from langchain_community.tools import TavilySearchResults
import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI



image_nav_prompt = open("../resources/prompt.txt", "r").read()
search_tool_description = open("../resources/search_tool.txt", "r").read()

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

search_tool = TavilySearchResults(api_key="TAVILY_API_KEY", description = search_tool_description)

tools = [
    Tool(name="Search Tool", func=search_tool.run, description="Search for specific locations using Tavily and retrieve relevant information."),
    Tool(name="Get Surroundings", func=get_surroundings_description, description="Provide a detailed visual description of a location using Google Street View. Takes 'location', 'heading', and 'pitch' as inputs."),
    Tool(name="Places Nearby", func=places_nearby, description="Fetch a list of nearby places based on a query. Requires 'query', 'radius' in meters, 'location' as latitude,longitude format, "
            "and 'limit' as the maximum number of results.")
]

llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o")


agent = initialize_agent(
    tools,
    llm,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

query = "What restaurants are near 40.712776,-74.005974 within 5000 meters?"

# The agent will use the appropriate tool based on the query
response = agent.run(query)
print(response)