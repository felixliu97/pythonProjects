import sys
from itertools import combinations
import math

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            grid = [line.strip() for line in f.readlines()]
            
        freq_map = {}
        rows = len(grid)
        cols = len(grid[0])
        
        for r in range(rows):
            for c in range(cols):
                char = grid[r][c]
                if char != '.':
                    if char not in freq_map:
                        freq_map[char] = []
                    freq_map[char].append((r, c))
                    
        return grid, freq_map, rows, cols
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def run_tests():
    print("Running tests...")
    
    example_input = [
        "............",
        "........0...",
        ".....0......",
        ".......0....",
        "....0.......",
        "......A.....",
        "............",
        "............",
        "........A...",
        ".........A..",
        "............",
        "............"
    ]
    
    grid = example_input
    freq_map = {}
    rows = len(grid)
    cols = len(grid[0])
    
    for r in range(rows):
        for c in range(cols):
            char = grid[r][c]
            if char != '.':
                if char not in freq_map:
                    freq_map[char] = []
                freq_map[char].append((r, c))
                
    p1 = get_part1_result(freq_map, rows, cols)
    print(f"Test P1: {p1}")
    expected_p1 = 14
    if p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1}")
        
    p2 = get_part2_result(freq_map, rows, cols)
    print(f"Test P2: {p2}")
    expected_p2 = 34
    if p2 == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {p2}")
        
    print("✅ Tests completed!")

def get_part1_result(freq_map, rows, cols):
    antinodes = set()
    for freq, positions in freq_map.items():
        if len(positions) < 2:
            continue
            
        for p1, p2 in combinations(positions, 2):
            r1, c1 = p1
            r2, c2 = p2
            
            dr = r2 - r1
            dc = c2 - c1
            
            ar1 = r1 - dr
            ac1 = c1 - dc
            ar2 = r2 + dr
            ac2 = c2 + dc
            
            if 0 <= ar1 < rows and 0 <= ac1 < cols:
                antinodes.add((ar1, ac1))
            if 0 <= ar2 < rows and 0 <= ac2 < cols:
                antinodes.add((ar2, ac2))
    return len(antinodes)

def get_part2_result(freq_map, rows, cols):
    antinodes = set()
    for freq, positions in freq_map.items():
        if len(positions) < 2:
            continue
            
        for p1, p2 in combinations(positions, 2):
            r1, c1 = p1
            r2, c2 = p2
            
            dr = r2 - r1
            dc = c2 - c1
            
            # Normalize vector
            divisor = math.gcd(dr, dc)
            norm_dr = dr // divisor
            norm_dc = dc // divisor
            
            # Start at p1 and go backwards
            curr_r, curr_c = r1, c1
            while 0 <= curr_r < rows and 0 <= curr_c < cols:
                antinodes.add((curr_r, curr_c))
                curr_r -= norm_dr
                curr_c -= norm_dc
            
            # Start at p1 + step and go forwards
            curr_r, curr_c = r1 + norm_dr, c1 + norm_dc
            while 0 <= curr_r < rows and 0 <= curr_c < cols:
                antinodes.add((curr_r, curr_c))
                curr_r += norm_dr
                curr_c += norm_dc
                
    return len(antinodes)

def solve_part1():
    print("--- Part 1 ---")
    grid, freq_map, rows, cols = parse_input("input-day8.txt")
    result = get_part1_result(freq_map, rows, cols)
    print(f"Result: {result}")

def solve_part2():
    print("--- Part 2 ---")
    grid, freq_map, rows, cols = parse_input("input-day8.txt")
    result = get_part2_result(freq_map, rows, cols)
    print(f"Result: {result}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
