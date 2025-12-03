import math

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

def test_example():
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
    assert p1 == 3, f"Expected P1=3, got {p1}"
    assert p2 == 6, f"Expected P2=6, got {p2}"

if __name__ == "__main__":
    # Run example test
    test_example()
    
    # Run on full input
    try:
        with open("input-day1.txt", "r") as f:
            input_text = f.read()
        p1, p2 = solve(input_text)
        print(f"Puzzle Part 1: {p1}")
        print(f"Puzzle Part 2: {p2}")
    except FileNotFoundError:
        print("Error: input-day1.txt not found.")
