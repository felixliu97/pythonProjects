import sys
from collections import deque

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def solve_grid(grid, start_state):
    # state: (row, col, dr, dc)
    rows = len(grid)
    cols = len(grid[0])
    
    queue = deque([start_state])
    seen_states = {start_state}
    energized = {(start_state[0], start_state[1])}
    
    while queue:
        r, c, dr, dc = queue.popleft()
        
        # Determine movement logic
        # Current tile: grid[r][c]
        try:
            tile = grid[r][c]
        except IndexError:
             # Should not happen if we check bounds before adding
             continue
             
        next_dirs = []
        
        if tile == '.':
            next_dirs.append((dr, dc))
        elif tile == '/':
            # (0, 1) -> (-1, 0) : Right to Up
            # (0, -1) -> (1, 0) : Left to Down
            # (1, 0) -> (0, -1) : Down to Left
            # (-1, 0) -> (0, 1) : Up to Right
            next_dirs.append((-dc, -dr))
        elif tile == '\\':
            # (0, 1) -> (1, 0) : Right to Down
            # (0, -1) -> (-1, 0) : Left to Up
            # (1, 0) -> (0, 1) : Down to Right
            # (-1, 0) -> (0, -1) : Up to Left
            next_dirs.append((dc, dr))
        elif tile == '|':
            if dc != 0: # Moving horizontal, split
                next_dirs.append((-1, 0)) # Up
                next_dirs.append((1, 0))  # Down
            else: # Moving vertical, pass
                next_dirs.append((dr, dc))
        elif tile == '-':
            if dr != 0: # Moving vertical, split
                next_dirs.append((0, -1)) # Left
                next_dirs.append((0, 1))  # Right
            else:
                next_dirs.append((dr, dc))
                
        for ndr, ndc in next_dirs:
            nr, nc = r + ndr, c + ndc
            if 0 <= nr < rows and 0 <= nc < cols:
                state = (nr, nc, ndr, ndc)
                if state not in seen_states:
                    seen_states.add(state)
                    energized.add((nr, nc))
                    queue.append(state)
                    
    return len(energized)

def solve(data):
    grid = data.split('\n')
    rows = len(grid)
    cols = len(grid[0])
    
    # Part 1: (0,0) moving Right (0, 1)
    # Be careful: start is (0,0) ENTERING from outside? No, beam enters at (0,0).
    # But movement logic usually applies to current tile.
    # We should initialize with the state AT (0,0) facing direction?
    # Actually, light enters top-left heading Right.
    # So we process (0,0) with direction (0,1).
    p1 = solve_grid(grid, (0, 0, 0, 1))
    
    # Part 2: Try all starts
    max_val = 0
    
    starts = []
    # Top Row (heading Down)
    for c in range(cols):
        starts.append((0, c, 1, 0))
    # Bottom Row (heading Up)
    for c in range(cols):
        starts.append((rows-1, c, -1, 0))
    # Left Col (heading Right)
    for r in range(rows):
        starts.append((r, 0, 0, 1))
    # Right Col (heading Left)
    for r in range(rows):
        starts.append((r, cols-1, 0, -1))
        
    for start in starts:
        val = solve_grid(grid, start)
        max_val = max(max_val, val)
        
    return p1, max_val

def run_tests():
    print("Running tests...")
    example = r""".|...\....
|.-.\.....
.....|-...
........|.
..........
.........\
..../.\\..
.-.-/..|..
.|....-|.\
..//.|...."""
    
    p1, p2 = solve(example)
    expected_p1 = 46
    expected_p2 = 51
    
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
    data = parse_input("2023-day16.txt")
    p1, p2 = solve(data)
    print("--- Part 1 ---")
    print(f"Result: {p1}")
    print("--- Part 2 ---")
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1_and_2()
