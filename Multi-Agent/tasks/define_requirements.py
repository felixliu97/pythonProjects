from crewai import Task
from agents.product_manager import product_manager

define_requirements_task = Task(
    description="""
    Create a comprehensive Product Requirements Document (PRD) for a Monopoly board game.
    
    The PRD must include:
    
    1. **Project Overview**
       - Brief description of the Monopoly game
       - Target platform (Python CLI or simple GUI)
       - Core objectives
    
    2. **Game Rules Summary**
       - Board layout (40 spaces)
       - Property types (streets, railroads, utilities)
       - Game flow (turns, dice rolling, movement)
       - Buying/selling properties
       - Rent calculation
       - Houses and hotels
       - Chance and Community Chest cards
       - Jail mechanics
       - Winning conditions (bankruptcy of all other players)
    
    3. **User Stories with Acceptance Criteria**
       - As a player, I can roll dice and move my token
       - As a player, I can buy unowned properties
       - As a player, I can pay rent when landing on owned properties
       - As a player, I can build houses/hotels
       - As a player, I can mortgage properties
       - As a player, I can trade with other players
       - etc.
    
    4. **Technical Requirements**
       - Python 3.10+
       - Object-oriented design
       - Modular architecture
       - Command-line interface for MVP
    
    5. **Out of Scope (for MVP)**
       - Graphical UI
       - Network multiplayer
       - Save/load game state
    
    6. **Success Metrics**
       - All core game rules implemented
       - 2-4 player support
       - Complete game loop from start to winner
    
    Save the PRD to: output/prd.md
    """,
    expected_output="A complete PRD in markdown format",
    agent=product_manager,
    output_file="output/prd.md"
)
