import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            content = f.read()
        
        reports = []
        for line in content.strip().split('\n'):
            if line.strip():
                reports.append(list(map(int, line.strip().split())))
        return reports
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def is_safe(report):
    if len(report) < 2:
        return True
    
    # Check differences
    diffs = [b - a for a, b in zip(report, report[1:])]
    
    # Check strictly increasing or strictly decreasing
    is_increasing = all(d > 0 for d in diffs)
    is_decreasing = all(d < 0 for d in diffs)
    
    if not (is_increasing or is_decreasing):
        return False
        
    # Check absolute difference range [1, 3]
    is_valid_range = all(1 <= abs(d) <= 3 for d in diffs)
    
    return is_valid_range

def is_safe_dampener(report):
    if is_safe(report):
        return True
    
    # Try removing each level
    for i in range(len(report)):
        modified_report = report[:i] + report[i+1:]
        if is_safe(modified_report):
            return True
            
    return False

def run_tests():
    print("Running tests...")
    
    example_input = """7 6 4 2 1
1 2 7 8 9
9 7 6 2 1
1 3 2 4 5
8 6 4 4 1
1 3 6 7 9"""
    
    reports = []
    for line in example_input.strip().split('\n'):
        reports.append(list(map(int, line.strip().split())))
        
    # Test Part 1
    safe_count = sum(1 for r in reports if is_safe(r))
    print(f"Test Part 1 Result: {safe_count} (Expected 2)")
    expected_p1 = 2
    if safe_count == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {safe_count}")

    # Test Part 2
    safe_count_p2 = sum(1 for r in reports if is_safe_dampener(r))
    print(f"Test Part 2 Result: {safe_count_p2} (Expected 4)")
    expected_p2 = 4
    if safe_count_p2 == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {safe_count_p2}")
        
    print("✅ Tests completed!")

def solve_part1():
    print("--- Part 1 ---")
    reports = parse_input("input-day2.txt")
    safe_count = sum(1 for r in reports if is_safe(r))
    print(f"Result: {safe_count}")

def solve_part2():
    print("--- Part 2 ---")
    reports = parse_input("input-day2.txt")
    safe_count = sum(1 for r in reports if is_safe_dampener(r))
    print(f"Result: {safe_count}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
