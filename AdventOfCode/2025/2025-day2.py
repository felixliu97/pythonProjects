import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            # Join lines just in case, though problem says single line.
            # Remove any whitespace including newlines
            content = "".join(line.strip() for line in f)
            return content.split(',')
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def is_invalid_part1(n):
    s = str(n)
    if len(s) % 2 != 0:
        return False
    mid = len(s) // 2
    return s[:mid] == s[mid:]

def is_invalid_part2(n):
    s = str(n)
    # Check if s is formed by repeating a substring at least twice.
    # This is true if and only if s is found in (s + s)[1:-1].
    return s in (s + s)[1:-1]

def solve(ranges_str_list):
    total_invalid_sum_part1 = 0
    total_invalid_sum_part2 = 0
    
    for r in ranges_str_list:
        if not r: continue
        try:
            start_str, end_str = r.split('-')
            start = int(start_str)
            end = int(end_str)
            
            for num in range(start, end + 1):
                if is_invalid_part1(num):
                    total_invalid_sum_part1 += num
                if is_invalid_part2(num):
                    total_invalid_sum_part2 += num
        except ValueError:
            print(f"Skipping invalid range format: {r}")
            continue

    return total_invalid_sum_part1, total_invalid_sum_part2

def run_tests():
    print("Running tests...")
    
    example_input_str = """
11-22,95-115,998-1012,1188511880-1188511890,222220-222224,
1698522-1698528,446443-446449,38593856-38593862,565653-565659,
824824821-824824827,2121212118-2121212124
"""
    # Clean up example input which might have newlines
    example_ranges = "".join(example_input_str.split()).split(',')
    
    p1, p2 = solve(example_ranges)
    print(f"Example Part 1 Sum: {p1}")
    print(f"Example Part 2 Sum: {p2}")
    
    expected_p1 = 1227775554
    if p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1}")
        
    expected_p2 = 4174379265
    if p2 == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {p2}")

    print("✅ Tests completed!")

def solve_part1():
    print("--- Part 1 ---")
    ranges = parse_input('2025-day2.txt')
    p1, _ = solve(ranges)
    print(f"Result: {p1}")

def solve_part2():
    print("--- Part 2 ---")
    ranges = parse_input('2025-day2.txt')
    _, p2 = solve(ranges)
    print(f"Result: {p2}")

if __name__ == '__main__':
    run_tests()
    solve_part1()
    solve_part2()
