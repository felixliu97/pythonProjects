from crewai import Agent
from crewai_tools import FileReadTool, FileWriterTool, DirectoryReadTool

# Initialize tools
file_read_tool = FileReadTool()
file_write_tool = FileWriterTool()
directory_read_tool = DirectoryReadTool()

from utils.llm_config import get_llm

developer = Agent(
    role="Senior Software Developer",
    goal="""Implement a fully functional Monopoly board game in Python based on 
    the Product Manager's requirements. Write clean, modular, and well-documented code.""",
    backstory="""You are a senior Python developer with 10+ years of experience 
    building games and interactive applications. You follow SOLID principles, 
    write comprehensive docstrings, and create maintainable code. You have 
    experience with object-oriented design patterns suitable for game development.""",
    tools=[file_read_tool, file_write_tool, directory_read_tool],
    verbose=True,
    allow_delegation=True,
    max_iter=10,
    llm=get_llm()
)
