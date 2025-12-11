import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            content = f.read()
            
        parts = content.split('\n\n')
        range_lines = parts[0].strip().splitlines()
        id_lines = parts[1].strip().splitlines() if len(parts) > 1 else []
        
        ranges = []
        for line in range_lines:
            if line.strip():
                start, end = map(int, line.strip().split('-'))
                ranges.append((start, end))
                
        ids = []
        for line in id_lines:
            if line.strip():
                ids.append(int(line.strip()))
                
        return ranges, ids
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def is_fresh(ingredient_id, ranges):
    for start, end in ranges:
        if start <= ingredient_id <= end:
            return True
    return False

def count_fresh_ids(ranges, ids):
    count = 0
    for i in ids:
        if is_fresh(i, ranges):
            count += 1
    return count

def calculate_total_fresh_range_size(ranges):
    if not ranges:
        return 0
        
    # Sort ranges by start value
    sorted_ranges = sorted(ranges, key=lambda x: x[0])
    
    merged_ranges = []
    current_start, current_end = sorted_ranges[0]
    
    for i in range(1, len(sorted_ranges)):
        next_start, next_end = sorted_ranges[i]
        
        # If overlapping or adjacent (e.g. 3-5 and 6-8 are adjacent integers)
        if next_start <= current_end + 1: 
            current_end = max(current_end, next_end)
        else:
            merged_ranges.append((current_start, current_end))
            current_start, current_end = next_start, next_end
            
    merged_ranges.append((current_start, current_end))
    
    total_fresh = 0
    for start, end in merged_ranges:
        total_fresh += (end - start + 1)
        
    return total_fresh

def run_tests():
    print("Running tests...")
    
    example_ranges_str = """
3-5
10-14
16-20
12-18
"""
    example_ids_str = """
1
5
8
11
17
32
"""
    # Simulate parsing
    ranges = []
    for line in example_ranges_str.strip().splitlines():
        start, end = map(int, line.split('-'))
        ranges.append((start, end))
        
    ids = [int(x) for x in example_ids_str.strip().splitlines()]
    
    print("Verifying Part 1 Example...")
    p1 = count_fresh_ids(ranges, ids)
    expected_p1 = 3
    if p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1}")
        
    print("Verifying Part 2 Example...")
    # Explanation:
    # 3-5 (3)
    # 10-14 (5)
    # 16-20 (5)
    # 12-18 (7) -> overlaps with 10-14 and 16-20
    # Combined: 
    # 3-5
    # 10-14 U 12-18 -> 10-18
    # 10-18 U 16-20 -> 10-20
    # Total: 3-5 (3 items) + 10-20 (11 items) = 14 items
    p2 = calculate_total_fresh_range_size(ranges)
    expected_p2 = 14
    if p2 == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {p2}")
        
    print("✅ Tests completed!")

def solve_part1():
    print("--- Part 1 ---")
    ranges, ids = parse_input('input-day5.txt')
    result = count_fresh_ids(ranges, ids)
    print(f"Result: {result}")

def solve_part2():
    print("--- Part 2 ---")
    ranges, _ = parse_input('input-day5.txt')
    result = calculate_total_fresh_range_size(ranges)
    print(f"Result: {result}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
