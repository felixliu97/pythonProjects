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
        print(f"Error: File {filename} not found.")
        return [], {}, 0, 0

def solve(filename):
    grid, freq_map, rows, cols = parse_input(filename)
    if not grid:
        return 0, 0
        
    antinodes_p1 = set()
    antinodes_p2 = set()
    
    for freq, positions in freq_map.items():
        if len(positions) < 2:
            continue
            
        # Iterate over all unique pairs
        for p1, p2 in combinations(positions, 2):
            r1, c1 = p1
            r2, c2 = p2
            
            # Vector from p1 to p2
            dr = r2 - r1
            dc = c2 - c1
            
            # Part 1: Specific distance logic
            # P1 = A - D, P2 = B + D
            ar1_p1 = r1 - dr
            ac1_p1 = c1 - dc
            ar2_p1 = r2 + dr
            ac2_p1 = c2 + dc
            
            if 0 <= ar1_p1 < rows and 0 <= ac1_p1 < cols:
                antinodes_p1.add((ar1_p1, ac1_p1))
            if 0 <= ar2_p1 < rows and 0 <= ac2_p1 < cols:
                antinodes_p1.add((ar2_p1, ac2_p1))
                
            # Part 2: All collinear points
            # Normalize vector
            divisor = math.gcd(dr, dc)
            norm_dr = dr // divisor
            norm_dc = dc // divisor
            
            # Start at p1 and go backwards
            curr_r, curr_c = r1, c1
            while 0 <= curr_r < rows and 0 <= curr_c < cols:
                antinodes_p2.add((curr_r, curr_c))
                curr_r -= norm_dr
                curr_c -= norm_dc
            
            # Start at p1 (actually p1 + norm) and go forwards
            curr_r, curr_c = r1 + norm_dr, c1 + norm_dc
            while 0 <= curr_r < rows and 0 <= curr_c < cols:
                antinodes_p2.add((curr_r, curr_c))
                curr_r += norm_dr
                curr_c += norm_dc
                
    return len(antinodes_p1), len(antinodes_p2)

def test():
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
                
    # Logic copied for testing
    ap1 = set()
    ap2 = set()
    for freq, positions in freq_map.items():
        if len(positions) < 2: continue
        for p1, p2 in combinations(positions, 2):
            r1, c1 = p1
            r2, c2 = p2
            dr = r2 - r1
            dc = c2 - c1
            
            # P1
            if 0 <= r1 - dr < rows and 0 <= c1 - dc < cols: ap1.add((r1 - dr, c1 - dc))
            if 0 <= r2 + dr < rows and 0 <= c2 + dc < cols: ap1.add((r2 + dr, c2 + dc))
            
            # P2
            div = math.gcd(dr, dc)
            ndr, ndc = dr // div, dc // div
            
            cr, cc = r1, c1
            while 0 <= cr < rows and 0 <= cc < cols:
                ap2.add((cr, cc))
                cr -= ndr
                cc -= ndc
            
            cr, cc = r1 + ndr, c1 + ndc
            while 0 <= cr < rows and 0 <= cc < cols:
                ap2.add((cr, cc))
                cr += ndr
                cc += ndc
                
    print(f"Test P1: {len(ap1)}")
    assert len(ap1) == 14
    print(f"Test P2: {len(ap2)}")
    assert len(ap2) == 34

if __name__ == "__main__":
    test()
    print("Tests passed!")
    p1, p2 = solve("input-day8.txt")
    print(f"Part 1 Result: {p1}")
    print(f"Part 2 Result: {p2}")
