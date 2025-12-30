from crewai import Agent
from crewai_tools import FileReadTool, DirectoryReadTool

# Initialize tools
file_read_tool = FileReadTool()
directory_read_tool = DirectoryReadTool()

from utils.llm_config import get_llm

qa_engineer = Agent(
    role="QA Engineer",
    goal="""Thoroughly test the Monopoly game implementation to ensure it meets 
    all requirements and acceptance criteria. Identify bugs, edge cases, and 
    potential improvements.""",
    backstory="""You are a meticulous QA engineer who has tested numerous game 
    applications. You excel at finding edge cases, writing comprehensive test 
    scenarios, and ensuring game logic is bug-free. You understand Monopoly 
    rules deeply and can verify correct implementation of game mechanics.""",
    tools=[file_read_tool, directory_read_tool],
    verbose=True,
    allow_delegation=True,
    max_iter=5,
    llm=get_llm()
)
