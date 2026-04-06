import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def tilt_north(grid):
    rows = len(grid)
    cols = len(grid[0])
    new_grid = [list(row) for row in grid]
    
    for c in range(cols):
        # Process each column
        # Move 'O's as far north as possible
        next_open = 0
        for r in range(rows):
            char = new_grid[r][c]
            if char == 'O':
                if r != next_open:
                    new_grid[next_open][c] = 'O'
                    new_grid[r][c] = '.'
                next_open += 1
            elif char == '#':
                next_open = r + 1
            # If '.', next_open stays same
            
    return tuple("".join(row) for row in new_grid)

def tilt_west(grid):
    rows = len(grid)
    cols = len(grid[0])
    new_grid = [list(row) for row in grid]
    
    for r in range(rows):
        next_open = 0
        for c in range(cols):
            char = new_grid[r][c]
            if char == 'O':
                if c != next_open:
                    new_grid[r][next_open] = 'O'
                    new_grid[r][c] = '.'
                next_open += 1
            elif char == '#':
                next_open = c + 1
                
    return tuple("".join(row) for row in new_grid)

def tilt_south(grid):
    rows = len(grid)
    cols = len(grid[0])
    new_grid = [list(row) for row in grid]
    
    for c in range(cols):
        # Process each column
        next_open = rows - 1
        for r in range(rows - 1, -1, -1):
            char = new_grid[r][c]
            if char == 'O':
                if r != next_open:
                    new_grid[next_open][c] = 'O'
                    new_grid[r][c] = '.'
                next_open -= 1
            elif char == '#':
                next_open = r - 1
                
    return tuple("".join(row) for row in new_grid)

def tilt_east(grid):
    rows = len(grid)
    cols = len(grid[0])
    new_grid = [list(row) for row in grid]
    
    for r in range(rows):
        next_open = cols - 1
        for c in range(cols - 1, -1, -1):
            char = new_grid[r][c]
            if char == 'O':
                if c != next_open:
                    new_grid[r][next_open] = 'O'
                    new_grid[r][c] = '.'
                next_open -= 1
            elif char == '#':
                next_open = c - 1
                
    return tuple("".join(row) for row in new_grid)

def cycle(grid):
    grid = tilt_north(grid)
    grid = tilt_west(grid)
    grid = tilt_south(grid)
    grid = tilt_east(grid)
    return grid

def calculate_load(grid):
    rows = len(grid)
    total_load = 0
    for r, row in enumerate(grid):
        load_per_rock = rows - r
        count = row.count('O')
        total_load += count * load_per_rock
    return total_load

def solve(data):
    grid = tuple(data.split('\n'))
    
    # Part 1
    p1_grid = tilt_north(grid)
    p1 = calculate_load(p1_grid)
    
    # Part 2
    seen = {}
    history = []
    
    current = grid
    target = 1000000000
    
    i = 0
    while i < target:
        if current in seen:
            cycle_start_index = seen[current]
            cycle_len = i - cycle_start_index
            remaining = target - i
            
            # Skip iterations
            skip = (remaining // cycle_len) * cycle_len
            i += skip
            
            # Clear seen to avoid re-triggering logic immediately (or just break if exact match)
            # Actually, we just need to finish the remaining steps
            # seen = {} # Don't clear, just continue loop. The 'current' check will fail or pass but `i < target` handles it.
            # But if we skip, `i` jumps close to target.
            
            # Break the cycle detection part and finish
            # Or simpler:
            remaining_after_skip = remaining % cycle_len
            
            # The state at `target` is the same as state at `cycle_start_index + remaining_after_skip`
            # Look up history
            final_state = history[cycle_start_index + remaining_after_skip]
            return p1, calculate_load(final_state)
            
        seen[current] = i
        history.append(current)
        current = cycle(current)
        i += 1
        
    return p1, calculate_load(current)

def run_tests():
    print("Running tests...")
    example = """O....#....
O.OO#....#
.....##...
OO.#O....O
.O.....O#.
O.#..O.#.#
..O..#O..O
.......O..
#....###..
#OO..#...."""
    
    p1, p2 = solve(example)
    expected_p1 = 136
    expected_p2 = 64
    
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
    data = parse_input("2023-day14.txt")
    p1, p2 = solve(data)
    print("--- Part 1 ---")
    print(f"Result: {p1}")
    print("--- Part 2 ---")
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1_and_2()
