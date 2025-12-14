import sys
import re

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def run_tests():
    print("Running tests...")
    
    # Part 1 Example
    example_p1 = """1abc2
pqr3stu8vwx
a1b2c3d4e5f
treb7uchet"""
    
    expected_p1 = 142
    result_p1 = solve_calibration(example_p1)
    
    if result_p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {result_p1}")

    # Part 2 Example
    example_p2 = """two1nine
eightwothree
abcone2threexyz
xtwone3four
4nineeightseven2
zoneight234
7pqrstsixteen"""
    
    expected_p2 = 281
    result_p2 = solve_calibration_v2(example_p2)
    
    if result_p2 == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {result_p2}")
        
    print("✅ Tests completed!")

def solve_calibration(data):
    lines = data.split('\n')
    total = 0
    for line in lines:
        digits = re.findall(r'\d', line)
        if digits:
            total += int(digits[0] + digits[-1])
    return total

def solve_calibration_v2(data):
    lines = data.split('\n')
    total = 0
    # Map words to digits. Note that overlaps should be handled carefully.
    # The problem says: "eighthree" counts as 8 and 3?
    # "one, two, three, four, five, six, seven, eight, and nine"
    
    # Actually, standard regex findall doesn't handle overlapping matches like "eighthree" -> 8, 3.
    # But usually lookahead can help.
    
    digit_map = {
        'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
        'six': '6', 'seven': '7', 'eight': '8', 'nine': '9'
    }
    
    for line in lines:
        # We need to find the FIRST digit and LAST digit.
        # "one" allows finding words.
        
        # Strategy: Search from left for first, search from right for last (or generally find all overlapping).
        # To find overlapping with regex in python require lookahead ?=
        
        regex = r'(?=(\d|one|two|three|four|five|six|seven|eight|nine))'
        matches = re.findall(regex, line)
        
        if matches:
            first_val = matches[0]
            last_val = matches[-1]
            
            if first_val in digit_map: first_val = digit_map[first_val]
            if last_val in digit_map: last_val = digit_map[last_val]
            
            total += int(first_val + last_val)
            
    return total

def solve_part1():
    print("--- Part 1 ---")
    data = parse_input("2023-day1.txt")
    result = solve_calibration(data)
    print(f"Result: {result}")

def solve_part2():
    print("--- Part 2 ---")
    data = parse_input("2023-day1.txt")
    result = solve_calibration_v2(data)
    print(f"Result: {result}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
