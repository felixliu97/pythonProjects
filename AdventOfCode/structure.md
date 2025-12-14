# Project Structure Guidelines

All Python solution files (`.py`) in the `AdventOfCode` directory must adhere to the following structure to ensure consistency.

## Prerequisites & structure

### Event Details
- **Start Year**: 2015
- **Duration**: 
  - Most years: 25 days (Dec 1 - Dec 25).
  - 2025: 12 days.
- **Problem Structure**:
  - Most days have 2 parts. 
  - Part 2 depends on completing Part 1.
  - The final day (Day 25) of some years may only have Part 1 (often requires 49 stars to complete).

### URLs
- **Problem URL**: `https://adventofcode.com/{year}/day/{day}` (e.g., `https://adventofcode.com/2021/day/1)
- **Input URL**: `https://adventofcode.com/{year}/day/{day}/input` (e.g., `https://adventofcode.com/2021/day/1/input)

### Naming Conventions
- **Input File**: `{year}-day{day}.txt` (e.g., `2021-day1.txt`). Must be downloaded from the **Input URL**.
- **Script File**: `{year}-day{day}.py` (e.g., `2021-day1.py`)

## Required Functions

Each file should contain at least the following three functions:

### 1. `run_tests()`
- **Purpose**: Runs examples provided in the problem description to verify logic.
- **Behavior**: Compares actual vs expected results. Prints specific error messages with "Expected X, Got Y" on failure.

### 2. `solve_part1()`
- **Purpose**: Solves Part 1 of the daily challenge.
- **Behavior**: Reads input, processes it, and prints the solution.

### 3. `solve_part2()`
- **Purpose**: Solves Part 2 of the daily challenge.
- **Behavior**: Reads input, processes it, and prints the solution.

## Template

```python
import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def run_tests():
    print("Running tests...")
    
    # Example Test Case
    # expected = ...
    # result = ...
    
    # if result == expected:
    #     print("✅ Part 1 Example passed!")
    # else:
    #     print(f"❌ Part 1 Example failed: Expected {expected}, Got {result}")
        
    print("✅ Tests completed!")

def solve_part1():
    print("--- Part 1 ---")
    # data = parse_input("input-dayXX.txt")
    # result = ...
    # print(f"Result: {result}")

def solve_part2():
    print("--- Part 2 ---")
    # data = parse_input("input-dayXX.txt")
    # result = ...
    # print(f"Result: {result}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
```
