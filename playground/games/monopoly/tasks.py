"""
CrewAI Tasks for Monopoly Game Development
Defines task templates for the development workflow.
"""
from crewai import Task
from agents import create_product_owner, create_developer, create_tester


def create_requirement_task(feature_request: str, product_owner) -> Task:
    """Task for Product Owner to analyze and define requirements."""
    return Task(
        description=f"""Analyze the following feature request and create detailed requirements:

Feature Request: {feature_request}

Your task:
1. Review the existing README.md (PRD) to understand current scope
2. Define user stories with acceptance criteria for this feature
3. Identify any dependencies or impacts on existing functionality
4. Prioritize sub-tasks if the feature is complex

Output a structured requirements document.""",
        expected_output="Detailed requirements with user stories and acceptance criteria",
        agent=product_owner
    )


def create_implementation_task(requirements: str, developer) -> Task:
    """Task for Developer to implement the feature."""
    return Task(
        description=f"""Implement the following requirements:

{requirements}

Your task:
1. Review the existing codebase structure (game.py, player.py, etc.)
2. Design the implementation approach
3. Write clean, documented Python code
4. Follow existing code patterns and style
5. Include docstrings and type hints

Output the implementation code with explanations.""",
        expected_output="Python code implementation with documentation",
        agent=developer
    )


def create_testing_task(implementation: str, tester) -> Task:
    """Task for Tester to validate the implementation."""
    return Task(
        description=f"""Test and validate the following implementation:

{implementation}

Your task:
1. Review the requirements and implementation
2. Create test cases covering happy path and edge cases
3. Identify any bugs or issues
4. Verify acceptance criteria are met
5. Suggest improvements if needed

Output a QA report with test results.""",
        expected_output="QA report with test cases and validation results",
        agent=tester
    )
