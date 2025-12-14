import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        equations = []
        for line in lines:
            if not line.strip(): continue
            parts = line.split(':')
            target = int(parts[0].strip())
            numbers = list(map(int, parts[1].strip().split()))
            equations.append((target, numbers))
        return equations
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def run_tests():
    print("Running tests...")
    
    example_input = [
        "190: 10 19",
        "3267: 81 40 27",
        "83: 17 5",
        "156: 15 6",
        "7290: 6 8 6 15",
        "161011: 16 10 13",
        "192: 17 8 14",
        "21037: 9 7 18 13",
        "292: 11 6 16 20"
    ]
    
    equations = []
    for line in example_input:
        parts = line.split(':')
        target = int(parts[0].strip())
        numbers = list(map(int, parts[1].strip().split()))
        equations.append((target, numbers))
        
    p1 = 0
    p2 = 0
    for target, nums in equations:
        if can_solve(target, nums[0], nums[1:], enable_concat=False):
            p1 += target
        
        if can_solve(target, nums[0], nums[1:], enable_concat=True):
            p2 += target
            
    print(f"Test Part 1: {p1}")
    expected_p1 = 3749
    if p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1}")
    
    print(f"Test Part 2: {p2}")
    expected_p2 = 11387
    if p2 == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {p2}")
    
    print("✅ Tests completed!")

def can_solve(target, current_val, remaining_nums, enable_concat=False):
    if current_val > target:
        return False
        
    if not remaining_nums:
        return current_val == target
    
    next_num = remaining_nums[0]
    rest = remaining_nums[1:]
    
    # Try addition
    if can_solve(target, current_val + next_num, rest, enable_concat):
        return True
    
    # Try multiplication
    if can_solve(target, current_val * next_num, rest, enable_concat):
        return True
        
    # Try concatenation
    if enable_concat:
        concat_val = int(str(current_val) + str(next_num))
        if can_solve(target, concat_val, rest, enable_concat):
            return True
        
    return False

def solve_part1():
    print("--- Part 1 ---")
    equations = parse_input("2024-day7.txt")
    total = 0
    for target, nums in equations:
        if can_solve(target, nums[0], nums[1:], enable_concat=False):
            total += target
    print(f"Result: {total}")

def solve_part2():
    print("--- Part 2 ---")
    equations = parse_input("2024-day7.txt")
    total = 0
    for target, nums in equations:
        if can_solve(target, nums[0], nums[1:], enable_concat=True):
            total += target
    print(f"Result: {total}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
