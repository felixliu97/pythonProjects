"""
CrewAI Crew Orchestration for Monopoly Game Development
Main entry point to run the multi-agent workflow.
"""
import os
import sys
from dotenv import load_dotenv
from crewai import Crew, Process

from agents import create_product_owner, create_developer, create_tester
from tasks import create_requirement_task, create_implementation_task, create_testing_task

# Load environment variables
load_dotenv()


def run_development_crew(feature_request: str) -> str:
    """
    Run the development crew to implement a feature.
    
    Args:
        feature_request: Description of the feature to implement
        
    Returns:
        Final output from the crew
    """
    # Create agents
    product_owner = create_product_owner()
    developer = create_developer()
    tester = create_tester()
    
    # Create tasks
    requirement_task = create_requirement_task(feature_request, product_owner)
    implementation_task = create_implementation_task(
        "Requirements from previous task", developer
    )
    testing_task = create_testing_task(
        "Implementation from previous task", tester
    )
    
    # Set task dependencies
    implementation_task.context = [requirement_task]
    testing_task.context = [requirement_task, implementation_task]
    
    # Create crew
    crew = Crew(
        agents=[product_owner, developer, tester],
        tasks=[requirement_task, implementation_task, testing_task],
        process=Process.sequential,
        verbose=True
    )
    
    # Execute
    result = crew.kickoff()
    return result


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python crew.py '<feature request>'")
        print("Example: python crew.py 'Add AI player support'")
        sys.exit(1)
    
    feature_request = sys.argv[1]
    
    print("=" * 60)
    print("  MONOPOLY DEVELOPMENT CREW")
    print("=" * 60)
    print(f"\nFeature Request: {feature_request}\n")
    print("-" * 60)
    
    result = run_development_crew(feature_request)
    
    print("\n" + "=" * 60)
    print("  FINAL OUTPUT")
    print("=" * 60)
    print(result)


if __name__ == "__main__":
    main()
