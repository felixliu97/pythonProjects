"""
CrewAI Agents for Monopoly Game Development
Defines Product Owner, Developer, and Tester roles.
"""
from crewai import Agent
from crewai_tools import FileReadTool, DirectoryReadTool

# Tools for agents
file_reader = FileReadTool()
dir_reader = DirectoryReadTool()


def create_product_owner() -> Agent:
    """Product Owner agent - defines requirements and priorities."""
    return Agent(
        role="Product Owner",
        goal="Define clear requirements, prioritize features, and ensure the game meets user expectations",
        backstory="""You are an experienced Product Owner who has shipped multiple successful 
        games. You understand both business needs and technical constraints. You excel at 
        writing clear user stories and acceptance criteria.""",
        tools=[file_reader, dir_reader],
        verbose=True,
        allow_delegation=True
    )


def create_developer() -> Agent:
    """Developer agent - implements features and writes code."""
    return Agent(
        role="Senior Python Developer",
        goal="Implement high-quality, maintainable Python code following best practices",
        backstory="""You are a senior Python developer with expertise in game development,
        Tkinter GUI, and clean architecture. You write well-documented, tested code and
        follow SOLID principles.""",
        tools=[file_reader, dir_reader],
        verbose=True,
        allow_delegation=False
    )


def create_tester() -> Agent:
    """Tester agent - validates quality and writes tests."""
    return Agent(
        role="QA Engineer",
        goal="Ensure the game is bug-free and meets all acceptance criteria",
        backstory="""You are a meticulous QA engineer who finds edge cases others miss.
        You write comprehensive test cases and validate that implementations match
        requirements exactly.""",
        tools=[file_reader, dir_reader],
        verbose=True,
        allow_delegation=False
    )
