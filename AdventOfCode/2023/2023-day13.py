import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def find_reflection(pattern, ignore_val=None):
    # Returns 100 * row_idx (horizontal) or col_idx (vertical)
    # ignore_val is to skip the original reflection in part 2
    
    rows = pattern
    cols = ["".join(rows[r][c] for r in range(len(rows))) for c in range(len(rows[0]))]
    
    # Check horizontal
    for r in range(1, len(rows)):
        # Reflection line between r-1 and r
        # Rows above: 0..r-1 (reversed)
        # Rows below: r..len-1
        
        above = rows[:r][::-1]
        below = rows[r:]
        
        length = min(len(above), len(below))
        if above[:length] == below[:length]:
            val = 100 * r
            if val != ignore_val:
                return val
            
    # Check vertical
    for c in range(1, len(cols)):
        left = cols[:c][::-1]
        right = cols[c:]
        
        length = min(len(left), len(right))
        if left[:length] == right[:length]:
            val = c
            if val != ignore_val:
                return val
            
    return 0

def solve_part2_pattern(pattern, original_val):
    # Try flipping each char
    # '.' <-> '#'
    # Check if new reflection exists
    
    for r in range(len(pattern)):
        for c in range(len(pattern[0])):
            # Flip
            row_list = list(pattern[r])
            row_list[c] = '.' if row_list[c] == '#' else '#'
            new_pattern = list(pattern)
            new_pattern[r] = "".join(row_list)
            
            val = find_reflection(new_pattern, ignore_val=original_val)
            if val > 0 and val != original_val:
                return val
    return 0

def solve(data):
    patterns = data.split('\n\n')
    sum_p1 = 0
    sum_p2 = 0
    
    for p in patterns:
        grid = [line.strip() for line in p.strip().split('\n')]
        val1 = find_reflection(grid)
        sum_p1 += val1
        
        val2 = solve_part2_pattern(grid, val1)
        sum_p2 += val2
        
    return sum_p1, sum_p2

def run_tests():
    print("Running tests...")
    example = """#.##..##.
..#.##.#.
##......#
##......#
..#.##.#.
..##..##.
#.#.##.#.

#...##..#
#....#..#
..##..###
#####.##.
#####.##.
..##..###
#....#..#"""
    
    p1, p2 = solve(example)
    expected_p1 = 405
    expected_p2 = 400
    
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
    data = parse_input("2023-day13.txt")
    p1, p2 = solve(data)
    print("--- Part 1 ---")
    print(f"Result: {p1}")
    print("--- Part 2 ---")
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1_and_2()
