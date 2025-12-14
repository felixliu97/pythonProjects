import sys
import itertools

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def solve(data, factor=2):
    lines = data.split('\n')
    rows = len(lines)
    cols = len(lines[0])
    
    galaxies = []
    
    for r, line in enumerate(lines):
        for c, char in enumerate(line):
            if char == '#':
                galaxies.append((r, c))
                
    empty_rows = [all(c == '.' for c in line) for line in lines]
    empty_cols = [all(lines[r][c] == '.' for r in range(rows)) for c in range(cols)]
    
    # Calculate offsets
    # row_map[r] = new_r
    
    row_map = []
    current_r = 0
    for r in range(rows):
        row_map.append(current_r)
        if empty_rows[r]:
            current_r += factor
        else:
            current_r += 1
            
    col_map = []
    current_c = 0
    for c in range(cols):
        col_map.append(current_c)
        if empty_cols[c]:
            current_c += factor
        else:
            current_c += 1
            
    # Transform galaxies
    expanded_galaxies = []
    for r, c in galaxies:
        expanded_galaxies.append((row_map[r], col_map[c]))
        
    # Sum distances
    total_dist = 0
    for g1, g2 in itertools.combinations(expanded_galaxies, 2):
        dist = abs(g1[0] - g2[0]) + abs(g1[1] - g2[1])
        total_dist += dist
        
    return total_dist

def run_tests():
    print("Running tests...")
    example = """...#......
.......#..
#.........
..........
......#...
.#........
.........#
..........
.......#..
#...#....."""
    
    p1 = solve(example, factor=2)
    expected_p1 = 374
    
    if p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1}")
        
    p2_10 = solve(example, factor=10)
    expected_p2_10 = 1030
    if p2_10 == expected_p2_10:
         print("✅ Part 2 (10x) Example passed!")
    else:
        print(f"❌ Part 2 (10x) Example failed: Expected {expected_p2_10}, Got {p2_10}")

    p2_100 = solve(example, factor=100)
    expected_p2_100 = 8410
    if p2_100 == expected_p2_100:
         print("✅ Part 2 (100x) Example passed!")
    else:
        print(f"❌ Part 2 (100x) Example failed: Expected {expected_p2_100}, Got {p2_100}")

    print("✅ Tests completed!")

def solve_part1_and_2():
    data = parse_input("2023-day11.txt")
    p1 = solve(data, factor=2)
    print("--- Part 1 ---")
    print(f"Result: {p1}")
    
    p2 = solve(data, factor=1000000)
    print("--- Part 2 ---")
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1_and_2()
