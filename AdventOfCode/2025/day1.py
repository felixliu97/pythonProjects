import sys
import math

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def solve(input_text):
    rotations = input_text.strip().splitlines()
    current_pos = 50
    
    # Part 1: Count zeros at the end of rotations
    zeros_part1 = 0
    
    # Part 2: Count all zeros passed
    zeros_part2 = 0
    # We track absolute position for Part 2 math
    abs_pos = 50
    
    for rotation in rotations:
        if not rotation:
            continue
            
        direction = rotation[0]
        amount = int(rotation[1:])
        
        if direction == 'L':
            # Part 1 update
            current_pos = (current_pos - amount) % 100
            
            # Part 2 update
            # Moving left: from abs_pos down to abs_pos - amount
            # We want multiples of 100 in range [end, start - 1]
            start = abs_pos
            end = abs_pos - amount
            count = math.floor((start - 1) / 100) - math.floor((end - 1) / 100)
            zeros_part2 += count
            abs_pos = end
            
        elif direction == 'R':
            # Part 1 update
            current_pos = (current_pos + amount) % 100
            
            # Part 2 update
            # Moving right: from abs_pos up to abs_pos + amount
            # We want multiples of 100 in range [start + 1, end]
            start = abs_pos
            end = abs_pos + amount
            count = math.floor(end / 100) - math.floor(start / 100)
            zeros_part2 += count
            abs_pos = end
            
        if current_pos == 0:
            zeros_part1 += 1
            
    return zeros_part1, zeros_part2

def run_tests():
    print("Running tests...")
    example_input = """
L68
L30
R48
L5
R60
L55
L1
L99
R14
L82
"""
    p1, p2 = solve(example_input)
    print(f"Example Part 1: {p1}")
    print(f"Example Part 2: {p2}")
    
    expected_p1 = 3
    if p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1}")
    
    expected_p2 = 6
    if p2 == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {p2}")
    
    print("✅ Tests completed!")

def solve_part1():
    print("--- Part 1 ---")
    input_text = parse_input("input-day1.txt")
    p1, _ = solve(input_text)
    print(f"Result: {p1}")

def solve_part2():
    print("--- Part 2 ---")
    input_text = parse_input("input-day1.txt")
    _, p2 = solve(input_text)
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
