import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            content = f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)
        
    return parse_content(content)

def parse_content(content):
    locks = []
    keys = []
    schematics = content.split('\n\n')
    
    for s in schematics:
        if not s.strip():
            continue
        is_lock, heights = parse_schematic(s)
        if is_lock:
            locks.append(heights)
        else:
            keys.append(heights)
            
    return locks, keys

def parse_schematic(schematic_str):
    rows = schematic_str.strip().split('\n')
    heights = []
    # Grid is 7 rows, 5 cols
    for col in range(5):
        count = 0
        for row in range(7):
            if rows[row][col] == '#':
                count += 1
        heights.append(count - 1)
    
    is_lock = (rows[0] == '#####')
    return is_lock, heights

def run_tests():
    print("Running tests...")
    
    example_input = """#####
.####
.####
.####
.#.#.
.#...
.....

#####
##.##
.#.##
...##
...#.
...#.
.....

.....
#....
#....
#...#
#.#.#
#.###
#####

.....
.....
#.#..
###..
###.#
###.#
#####

.....
.....
.....
#....
#.#..
#.#.#
#####"""
    
    locks_ex, keys_ex = parse_content(example_input)
    fits_ex = 0
    for lock in locks_ex:
        for key in keys_ex:
            if check_fit(lock, key):
                fits_ex += 1
                
    print(f"Test Example Fits: {fits_ex} (Expected 3)")
    expected_p1 = 3
    if fits_ex == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {fits_ex}")
        
    print("✅ Tests completed!")

def check_fit(lock, key):
    # Total available space is 5 unique rows between top and bottom rails.
    # Lock height + Key height <= 5 in every column.
    for i in range(5):
        if lock[i] + key[i] > 5:
            return False
    return True

def solve_part1():
    print("--- Part 1 ---")
    locks, keys = parse_input("input-day25.txt")
    
    valid_pairs = 0
    for lock in locks:
        for key in keys:
            if check_fit(lock, key):
                valid_pairs += 1
                
    print(f"Result: {valid_pairs}")

def solve_part2():
    print("--- Part 2 ---")
    print("Result: Functionality not available for Day 25 (Stars Check)")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
