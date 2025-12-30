from crewai import Task
from agents.developer import developer
from tasks.define_requirements import define_requirements_task

implement_code_task = Task(
    description="""
    Review the PRD created by the Product Manager and implement the Monopoly game.
    
    **Implementation Requirements:**
    
    1. **Core Classes to Create:**
       - `Game`: Main game controller
       - `Board`: Represents the 40-space board
       - `Player`: Player state and actions
       - `Property`: Base class for ownable spaces
       - `Street`: Properties that can have houses/hotels
       - `Railroad`: Railroad properties
       - `Utility`: Utility properties
       - `Card`: Chance and Community Chest cards
       - `Dice`: Dice rolling logic
    
    2. **Game Flow:**
       - Initialize game with 2-4 players
       - Each turn: roll dice, move, take action
       - Handle property purchases
       - Calculate and collect rent
       - Handle special spaces (Go, Jail, Free Parking, etc.)
       - Check for bankruptcy
       - Determine winner
    
    3. **Code Quality:**
       - Use type hints
       - Add comprehensive docstrings
       - Follow PEP 8 style
       - Modular file structure
    
    4. **Files to Create:**
       - `output/monopoly/game.py` - Main game logic
       - `output/monopoly/board.py` - Board and spaces
       - `output/monopoly/player.py` - Player class
       - `output/monopoly/property.py` - Property classes
       - `output/monopoly/cards.py` - Card classes
       - `output/monopoly/dice.py` - Dice class
       - `output/monopoly/constants.py` - Game constants
       - `output/monopoly/__init__.py` - Package init
       - `output/monopoly/main.py` - Entry point
    
    Focus on implementing the core game loop first, then add features incrementally.
    """,
    expected_output="Complete, working Monopoly game code saved to output/monopoly/",
    agent=developer,
    context=[define_requirements_task]
)
