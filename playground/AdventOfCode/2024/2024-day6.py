import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            grid = [list(line.strip()) for line in f.readlines()]
        return grid
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def run_tests():
    print("Running tests...")
    
    example_input = [
        "....#.....",
        ".........#",
        "..........",
        "..#.......",
        ".......#..",
        "..........",
        ".#..^.....",
        "........#.",
        "#.........",
        "......#..."
    ]
    grid = [list(line) for line in example_input]
    start_r, start_c = get_start_pos(grid)
    
    # Part 1 Test
    path_set = get_visited_path(grid, start_r, start_c)
    p1 = len(path_set)
    expected_p1 = 41
    
    if p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1}")
        
    # Part 2 Test
    # We need to re-parse grid or reset it because get_visited_path doesn't modify it, but let's be safe.
    # Actually get_visited_path logic is clean.
    # But for Part 2 logic, we define solve_logic_part2
    
    # Clean grid for Part 2 check
    grid = [list(line) for line in example_input]
    p2 = solve_logic_part2(grid, start_r, start_c, path_set)
    expected_p2 = 6
    
    if p2 == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {p2}")

    print("✅ Tests completed!")

def get_start_pos(grid):
    rows = len(grid)
    cols = len(grid[0])
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '^':
                return r, c
    return -1, -1

# Directions: Up, Right, Down, Left
DR = [-1, 0, 1, 0]
DC = [0, 1, 0, -1]

def get_visited_path(grid, start_r, start_c):
    rows = len(grid)
    cols = len(grid[0])
    direction = 0
    visited = set()
    r, c = start_r, start_c
    visited.add((r, c))
    
    while True:
        next_r = r + DR[direction]
        next_c = c + DC[direction]
        
        if not (0 <= next_r < rows and 0 <= next_c < cols):
            break
            
        if grid[next_r][next_c] == '#':
            direction = (direction + 1) % 4
        else:
            r, c = next_r, next_c
            visited.add((r, c))
    return visited

def check_loop(grid, start_r, start_c):
    rows = len(grid)
    cols = len(grid[0])
    direction = 0
    r, c = start_r, start_c
    
    visited_states = set()
    
    while True:
        state = (r, c, direction)
        if state in visited_states:
            return True # Loop detected
        visited_states.add(state)
        
        next_r = r + DR[direction]
        next_c = c + DC[direction]
        
        if not (0 <= next_r < rows and 0 <= next_c < cols):
            return False # Exited grid
            
        if grid[next_r][next_c] == '#':
            direction = (direction + 1) % 4
        else:
            r, c = next_r, next_c

def solve_logic_part2(grid, start_r, start_c, path_set):
    candidates = path_set.copy()
    if (start_r, start_c) in candidates:
        candidates.remove((start_r, start_c))
        
    loop_count = 0
    
    for r, c in candidates:
        # Place obstacle
        grid[r][c] = '#'
        
        if check_loop(grid, start_r, start_c):
            loop_count += 1
            
        # Backtrack
        grid[r][c] = '.'
        
    return loop_count

def solve_part1():
    print("--- Part 1 ---")
    grid = parse_input("2024-day6.txt")
    if not grid: return
    
    start_r, start_c = get_start_pos(grid)
    if start_r == -1: return
    
    path_set = get_visited_path(grid, start_r, start_c)
    print(f"Result: {len(path_set)}")

def solve_part2():
    print("--- Part 2 ---")
    grid = parse_input("2024-day6.txt")
    if not grid: return
    
    start_r, start_c = get_start_pos(grid)
    if start_r == -1: return

    # Need path from part 1 for optimization
    path_set = get_visited_path(grid, start_r, start_c)
    result = solve_logic_part2(grid, start_r, start_c, path_set)
    print(f"Result: {result}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
