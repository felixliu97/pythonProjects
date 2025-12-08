def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            grid = [list(line.strip()) for line in f.readlines()]
        return grid
    except FileNotFoundError:
        print(f"Error: File {filename} not found.")
        return []

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
    # State is (r, c, direction)
    
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

def solve(filename):
    grid = parse_input(filename)
    if not grid: return 0, 0
    
    start_r, start_c = get_start_pos(grid)
    if start_r == -1: return 0, 0
    
    # Part 1
    path_set = get_visited_path(grid, start_r, start_c)
    part1_result = len(path_set)
    
    # Part 2
    # Identify possible positions for obstruction.
    # Obstructions can only be placed on the original path (except likely not start)
    # Actually, placing an obstacle outside the path is useless.
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
        
    return part1_result, loop_count

def test():
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
    
    path_set = get_visited_path(grid, start_r, start_c)
    print(f"Test Part 1: {len(path_set)}")
    assert len(path_set) == 41
    
    candidates = path_set.copy()
    candidates.remove((start_r, start_c))
    
    loop_count = 0
    for r, c in candidates:
        grid[r][c] = '#'
        if check_loop(grid, start_r, start_c):
            loop_count += 1
        grid[r][c] = '.'
        
    print(f"Test Part 2: {loop_count}")
    assert loop_count == 6

if __name__ == "__main__":
    test()
    print("Tests passed!")
    p1, p2 = solve("input-day6.txt")
    print(f"Part 1 Result: {p1}")
    print(f"Part 2 Result: {p2}")
