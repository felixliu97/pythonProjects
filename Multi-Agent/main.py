"""
Multi-Agent Monopoly Development Crew

This script orchestrates a team of AI agents to develop a Monopoly board game:
- Product Manager: Defines requirements and user stories
- Developer: Implements the game code
- QA Engineer: Tests and validates the implementation

Usage:
    python main.py
"""

import os
from dotenv import load_dotenv
from crewai import Crew, Process

# Load environment variables
load_dotenv()

# Initialize LLM
from utils.llm_config import get_llm
from langchain_google_vertexai import VertexAIEmbeddings

llm = get_llm()

# Import agents
from agents.product_manager import product_manager
from agents.developer import developer
from agents.qa_engineer import qa_engineer

# Import tasks
from tasks.define_requirements import define_requirements_task
from tasks.implement_code import implement_code_task
from tasks.test_code import test_code_task


def main():
    """Run the Monopoly development crew."""
    
    # Create output directory if it doesn't exist
    os.makedirs("output/monopoly", exist_ok=True)
    
    print("=" * 60)
    print("🎲 MONOPOLY DEVELOPMENT CREW")
    print("=" * 60)
    print("\nAgents:")
    print("  - Product Manager: Defining requirements...")
    print("  - Developer: Implementing code...")
    print("  - QA Engineer: Testing and validation...")
    print("\n" + "=" * 60 + "\n")
    
    # Create the crew
    monopoly_crew = Crew(
        agents=[product_manager, developer, qa_engineer],
        tasks=[define_requirements_task, implement_code_task, test_code_task],
        process=Process.sequential,  # Tasks run in order
        verbose=True,
        memory=True,  # Enable memory for context retention
        embedder={
            "provider": "google",
            "config": {
                "model": "models/embedding-001",
            }
        },
        manager_llm=llm,
        function_calling_llm=llm
    )
    
    # Kick off the crew
    print("Starting the Monopoly Development Crew...\n")
    result = monopoly_crew.kickoff()
    
    print("\n" + "=" * 60)
    print("🎉 DEVELOPMENT COMPLETE!")
    print("=" * 60)
    print("\nOutput files:")
    print("  - output/prd.md (Product Requirements)")
    print("  - output/monopoly/ (Game Code)")
    print("  - output/qa_report.md (QA Report)")
    print("\n" + "=" * 60)
    
    return result


if __name__ == "__main__":
    result = main()
    print("\n\nFinal Result:")
    print(result)
