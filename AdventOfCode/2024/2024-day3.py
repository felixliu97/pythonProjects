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
    example_data_p1 = "xmul(2,4)%&mul[3,7]!@^do_not_mul(5,5)+mul(32,64]then(mul(11,8)mul(8,5))"
    expected_p1 = 161
    result_p1 = solve_logic_part1(example_data_p1)
    
    if result_p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {result_p1}")

    # Part 2 Example
    example_data_p2 = "xmul(2,4)&mul[3,7]!^don't()_mul(5,5)+mul(32,64](mul(11,8)undo()?mul(8,5))"
    expected_p2 = 48
    result_p2 = solve_logic_part2(example_data_p2)
    
    if result_p2 == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {result_p2}")
        
    print("✅ Tests completed!")

def solve_logic_part1(data):
    pattern = r"mul\((\d{1,3}),(\d{1,3})\)"
    matches = re.findall(pattern, data)
    total_sum = 0
    for x, y in matches:
        total_sum += int(x) * int(y)
    return total_sum

def solve_logic_part2(data):
    pattern = r"mul\((\d{1,3}),(\d{1,3})\)|do\(\)|don't\(\)"
    matches = re.finditer(pattern, data)
    total_sum = 0
    enabled = True 
    for match in matches:
        text = match.group(0)
        if text == "do()":
            enabled = True
        elif text == "don't()":
            enabled = False
        elif text.startswith("mul"):
            if enabled:
                x, y = match.group(1), match.group(2)
                total_sum += int(x) * int(y)
    return total_sum

def solve_part1():
    print("--- Part 1 ---")
    data = parse_input("2024-day3.txt")
    result = solve_logic_part1(data)
    print(f"Result: {result}")

def solve_part2():
    print("--- Part 2 ---")
    data = parse_input("2024-day3.txt")
    result = solve_logic_part2(data)
    print(f"Result: {result}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
