import sys
import re

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def is_symbol(char):
    return char != '.' and not char.isdigit()

def solve(data):
    lines = data.split('\n')
    rows = len(lines)
    cols = len(lines[0])
    
    # Store numbers: list of (value, row, start_col, end_col_exclusive)
    numbers = []
    # Store symbol locations: set of (r, c) or map to symbol char
    symbols = {}
    
    for r, line in enumerate(lines):
        # Find numbers
        for match in re.finditer(r'\d+', line):
            numbers.append((int(match.group()), r, match.start(), match.end()))
            
        # Find symbols
        for c, char in enumerate(line):
            if is_symbol(char):
                symbols[(r, c)] = char

    # Part 1
    part_sum = 0
    # Map (r, c) of symbol to list of adjacent numbers (for Part 2)
    # Gears: '*'
    gears_adjacent = {} # (r,c) -> [number_values]
    
    for val, r, c_start, c_end in numbers:
        is_part = False
        
        # Check surrounding box
        # Row: r-1 to r+1
        # Col: c_start-1 to c_end
        
        r_min = max(0, r - 1)
        r_max = min(rows - 1, r + 1)
        c_min = max(0, c_start - 1)
        c_max = min(cols - 1, c_end) # c_end is exclusive index, so checking up to c_end is correct for adjacent char
        
        for curr_r in range(r_min, r_max + 1):
            for curr_c in range(c_min, c_max + 1):
                # Don't check the number digits themselves (though they aren't in 'symbols' anyway)
                if (curr_r, curr_c) in symbols:
                    is_part = True
                    sym = symbols[(curr_r, curr_c)]
                    if sym == '*':
                        if (curr_r, curr_c) not in gears_adjacent:
                            gears_adjacent[(curr_r, curr_c)] = []
                        gears_adjacent[(curr_r, curr_c)].append(val)
                        
        if is_part:
            part_sum += val
            
    # Part 2
    ratio_sum = 0
    for pos, nums in gears_adjacent.items():
        if len(nums) == 2:
            ratio_sum += nums[0] * nums[1]
            
    return part_sum, ratio_sum

def run_tests():
    print("Running tests...")
    example = """467..114..
...*......
..35..633.
......#...
617*......
.....+.58.
..592.....
......755.
...$.*....
.664.598.."""
    
    p1, p2 = solve(example)
    expected_p1 = 4361
    expected_p2 = 467835
    
    if p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1}")
        
    if p2 == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {p2}")

    print("✅ Tests completed!")

def solve_part1_and_2():
    data = parse_input("2023-day3.txt")
    p1, p2 = solve(data)
    print("--- Part 1 ---")
    print(f"Result: {p1}")
    print("--- Part 2 ---")
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1_and_2()
