from crewai import Agent
from crewai_tools import SerperDevTool, FileReadTool, FileWriterTool

# Initialize tools
search_tool = SerperDevTool()
file_read_tool = FileReadTool()
file_write_tool = FileWriterTool()

from utils.llm_config import get_llm

product_manager = Agent(
    role="Product Manager",
    goal="""Define comprehensive requirements, user stories, and acceptance criteria 
    for developing a Monopoly board game implementation.""",
    backstory="""You are an experienced product manager who has shipped multiple 
    successful gaming products. You understand game mechanics, user experience, 
    and how to break down complex game rules into actionable development tasks. 
    You have deep knowledge of the Monopoly board game rules and mechanics.""",
    tools=[search_tool, file_read_tool, file_write_tool],
    verbose=True,
    allow_delegation=False,
    max_iter=5,
    llm=get_llm()
)
