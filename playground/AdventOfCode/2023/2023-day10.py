import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def solve(data):
    lines = data.split('\n')
    grid = [list(line) for line in lines]
    rows = len(grid)
    cols = len(grid[0])
    
    start_pos = None
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 'S':
                start_pos = (r, c)
                break
        if start_pos: break
        
    # Directions: N, E, S, W
    # Symbol connectivity
    # |: N, S
    # -: E, W
    # L: N, E
    # J: N, W
    # 7: S, W
    # F: S, E
    
    dirs = {
        '|': [(-1, 0), (1, 0)],
        '-': [(0, 1), (0, -1)],
        'L': [(-1, 0), (0, 1)],
        'J': [(-1, 0), (0, -1)],
        '7': [(1, 0), (0, -1)],
        'F': [(1, 0), (0, 1)],
        '.': [],
        'S': []
    }
    
    # Determine S type
    sr, sc = start_pos
    possible_s = {'|', '-', 'L', 'J', '7', 'F'}
    
    # Check North
    if sr > 0 and grid[sr-1][sc] in {'|', '7', 'F'}:
        # Neighbors connecting South are compatible 
        pass
    else:
        possible_s -= {'|', 'L', 'J'}
        
    # Check South
    if sr < rows - 1 and grid[sr+1][sc] in {'|', 'L', 'J'}:
        pass
    else:
        possible_s -= {'|', '7', 'F'}
        
    # Check West
    if sc > 0 and grid[sr][sc-1] in {'-', 'L', 'F'}:
        pass
    else:
        possible_s -= {'-', 'J', '7'}
        
    # Check East
    if sc < cols - 1 and grid[sr][sc+1] in {'-', 'J', '7'}:
        pass
    else:
        possible_s -= {'-', 'L', 'F'}
        
    s_type = list(possible_s)[0]
    grid[sr][sc] = s_type # Replace S with real type
    
    # BFS loop
    q = [(start_pos, 0)]
    visited = {start_pos: 0}
    max_dist = 0
    
    while q:
        (r, c), dist = q.pop(0)
        max_dist = max(max_dist, dist)
        
        sym = grid[r][c]
        for dr, dc in dirs[sym]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if (nr, nc) not in visited:
                    # Check if neighbor connects back (should be guaranteed by loop logic if we started right)
                    # Use 'dirs' to verify if (nr, nc) connects to (r, c)
                    # Actually, we rely on the loop being valid.
                    # But we must verify connection for S neighbors initially, and then just follow pipes.
                     
                    sym_n = grid[nr][nc]
                    if sym_n == '.': continue # Should not happen in loop
                    
                    # Verify back connection check:
                    connects_back = False
                    for ddr, ddc in dirs[sym_n]:
                        if (nr + ddr, nc + ddc) == (r, c):
                            connects_back = True
                            break
                    if connects_back:
                        visited[(nr, nc)] = dist + 1
                        q.append(((nr, nc), dist + 1))
                        
    # Part 2: Ray Casting
    inside_count = 0
    for r in range(rows):
        inside = False
        # Treat line scan.
        # We process segment by segment.
        # Wall passing logic:
        # | -> flips
        # L---7 -> flips
        # F---J -> flips
        # L---J -> no flip
        # F---7 -> no flip
        
        # When moving West to East:
        # If we encounter |, flip.
        # If we encounter F, wait for end.
        #   If end is J, flip.
        #   If end is 7, no flip.
        # If we encounter L, wait for end.
        #   If end is 7, flip.
        #   If end is J, no flip.
        
        # NOTE: Only count PIPES THAT ARE PART OF THE LOOP.
        # Treat non-loop pipes as '.'
        
        opening_corner = None
        
        for c in range(cols):
            val = grid[r][c]
            is_loop = (r, c) in visited
            
            if is_loop:
                if val == '|':
                    inside = not inside
                elif val == 'F':
                    opening_corner = 'F'
                elif val == 'L':
                    opening_corner = 'L'
                elif val == '7':
                    if opening_corner == 'L':
                        inside = not inside
                    opening_corner = None
                elif val == 'J':
                    if opening_corner == 'F':
                        inside = not inside
                    opening_corner = None
                elif val == '-':
                    pass
            else:
                if inside:
                    inside_count += 1
                    
    return max_dist, inside_count

def run_tests():
    print("Running tests...")
    # S is F (South, East)
    example = """.....
.S-7.
.|.|.
.L-J.
....."""
    
    p1, p2 = solve(example)
    expected_p1 = 4
    expected_p2 = 1 # Inner dot
    
    if p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1}")
        
    example2 = """...........
.S-------7.
.|F-----7|.
.||.....||.
.||.....||.
.|L-7.F-J|.
.|..|.|..|.
.L--J.L--J.
..........."""
    # 4 inside
    _, p2 = solve(example2)
    expected_p2 = 4
    if p2 == expected_p2:
         print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {p2}")

    print("✅ Tests completed!")

def solve_part1_and_2():
    data = parse_input("2023-day10.txt")
    p1, p2 = solve(data)
    print("--- Part 1 ---")
    print(f"Result: {p1}")
    print("--- Part 2 ---")
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1_and_2()
