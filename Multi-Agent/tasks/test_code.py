from crewai import Task
from agents.qa_engineer import qa_engineer
from tasks.define_requirements import define_requirements_task
from tasks.implement_code import implement_code_task

test_code_task = Task(
    description="""
    Review and test the Monopoly game code produced by the Developer.
    
    **Testing Checklist:**
    
    1. **Code Review:**
       - Read all source files in output/monopoly/
       - Verify code structure matches requirements
       - Check for proper OOP design
       - Verify type hints and docstrings
    
    2. **Functional Testing:**
       - Game initialization with 2-4 players
       - Dice rolling produces valid results (2-12)
       - Player movement wraps around the board correctly
       - Passing Go awards $200
       - Property purchase works correctly
       - Rent calculation is accurate
       - Jail mechanics work (rolling doubles, pay $50, use card)
       - Houses/hotels can be built on color sets
       - Bankruptcy detection works
       - Game ends when one player remains
    
    3. **Edge Cases:**
       - Player with $0 cannot buy
       - Cannot build houses without complete color set
       - Mortgaged properties don't collect rent
       - Double roll mechanics (extra turn, jail on 3rd)
    
    4. **Bug Reporting:**
       - Document any bugs found
       - Suggest fixes for each bug
       - Rate severity (Critical, Major, Minor)
    
    Save the QA report to: output/qa_report.md
    
    If critical bugs are found, delegate back to the Developer to fix them.
    """,
    expected_output="A comprehensive QA report in markdown format",
    agent=qa_engineer,
    context=[define_requirements_task, implement_code_task],
    output_file="output/qa_report.md"
)
