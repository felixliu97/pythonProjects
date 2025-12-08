
def parse_input(filename):
    with open(filename, 'r') as f:
        content = f.read()
    
    parts = content.split('\n\n')
    grid_str = parts[0].strip().split('\n')
    grid = [list(line) for line in grid_str]
    
    moves_str = parts[1].replace('\n', '').strip()
    
    return grid, moves_str

def find_robot(grid):
    for r, row in enumerate(grid):
        for c, val in enumerate(row):
            if val == '@':
                return r, c
    return None

def parse_map_string(map_str):
    # Remove empty lines and strip whitespace
    lines = [line.strip() for line in map_str.strip().split('\n') if line.strip()]
    return [list(line) for line in lines]

def move_robot(grid, moves):
    r, c = find_robot(grid)
    if r is None:
        raise ValueError("Robot not found!")

    rows = len(grid)
    cols = len(grid[0])
    
    directions = {
        '^': (-1, 0),
        'v': (1, 0),
        '<': (0, -1),
        '>': (0, 1)
    }
    
    for i, move in enumerate(moves):
        dr, dc = directions[move]
        nr, nc = r + dr, c + dc
        
        if not (0 <= nr < rows and 0 <= nc < cols):
            continue

        if grid[nr][nc] == '#':
            continue
        elif grid[nr][nc] == '.':
            grid[nr][nc] = '@'
            grid[r][c] = '.'
            r, c = nr, nc
        elif grid[nr][nc] == 'O':
            # Check if we can push the box(es)
            # Find the end of the chain of boxes
            cr, cc = nr, nc
            while 0 <= cr < rows and 0 <= cc < cols and grid[cr][cc] == 'O':
                cr += dr
                cc += dc
            
            if not (0 <= cr < rows and 0 <= cc < cols):
                continue # Pushed off edge (shouldn't happen with walls)

            if grid[cr][cc] == '.':
                grid[cr][cc] = 'O'
                grid[nr][nc] = '@'
                grid[r][c] = '.'
                r, c = nr, nc
            elif grid[cr][cc] == '#':
                continue
                
    return grid

def calculate_gps_sum(grid):
    total = 0
    for r, row in enumerate(grid):
        for c, val in enumerate(row):
            if val == 'O':
                total += 100 * r + c
    return total

def scale_map(grid):
    new_grid = []
    for row in grid:
        new_row = []
        for char in row:
            if char == '#':
                new_row.extend(['#', '#'])
            elif char == 'O':
                new_row.extend(['[', ']'])
            elif char == '.':
                new_row.extend(['.', '.'])
            elif char == '@':
                new_row.extend(['@', '.'])
        new_grid.append(new_row)
    return new_grid

def move_robot_part2(grid, moves):
    r, c = find_robot(grid)
    if r is None:
        raise ValueError("Robot not found!")

    rows = len(grid)
    cols = len(grid[0])
    
    directions = {
        '^': (-1, 0),
        'v': (1, 0),
        '<': (0, -1),
        '>': (0, 1)
    }
    
    for move in moves:
        dr, dc = directions[move]
        nr, nc = r + dr, c + dc
        
        if not (0 <= nr < rows and 0 <= nc < cols):
            continue

        target_char = grid[nr][nc]

        if target_char == '#':
            continue
        elif target_char == '.':
            grid[nr][nc] = '@'
            grid[r][c] = '.'
            r, c = nr, nc
        elif target_char in ['[', ']']:
            # Box pushing
            if dr == 0:
                # Horizontal Move (Left/Right)
                # Find the end of the chain
                cr, cc = nr, nc
                while 0 <= cr < rows and 0 <= cc < cols and grid[cr][cc] in ['[', ']']:
                    cc += dc
                
                if not (0 <= cc < cols): continue # Out of bounds
                if grid[cr][cc] == '#': continue # Blocked
                if grid[cr][cc] == '.':
                    # Shift everything from (nr, nc) to (cr, cc) (exclusive of cc initially, but inclusive of the shift)
                    # Actually standard shift:
                    # .. [ ] [ ] @ ..
                    # becomes
                    # .. [ ] [ ] . @ .. (Wait, shift direction is drift)
                    
                    # Iterating backward from the hole to the robot
                    curr_c = cc
                    while curr_c != nc:
                        prev_c = curr_c - dc
                        grid[cr][curr_c] = grid[cr][prev_c]
                        curr_c = prev_c
                    
                    grid[nr][nc] = '@'
                    grid[r][c] = '.'
                    r, c = nr, nc

            else:
                # Vertical Move (Up/Down) - The Tricky Part
                # BFS/DFS to find all connected boxes
                # Set of (r, c) for the LEFT '[' of each box
                boxes_to_move = set()
                queue = []
                
                # Normalize start box
                if target_char == '[':
                    queue.append((nr, nc))
                else:
                    queue.append((nr, nc - 1))
                
                possible = True
                while queue:
                    br, bc = queue.pop(0)
                    if (br, bc) in boxes_to_move:
                        continue
                    boxes_to_move.add((br, bc))
                    
                    # Check what this box pushes
                    # It occupies (br, bc) and (br, bc+1)
                    # It pushes into (br+dr, bc) and (br+dr, bc+1)
                    
                    next_positions = [(br + dr, bc), (br + dr, bc + 1)]
                    
                    for nr_check, nc_check in next_positions:
                        check_char = grid[nr_check][nc_check]
                        if check_char == '#':
                            possible = False
                            break
                        elif check_char == '[':
                            queue.append((nr_check, nc_check))
                        elif check_char == ']':
                            queue.append((nr_check, nc_check - 1))
                        # '.' is fine, ignores it
                    
                    if not possible:
                        break
                
                if possible:
                    # Move all boxes
                    # Sort to prevent overwriting
                    # If moving down (dr=1), process bottom-most first (descending r)
                    # If moving up (dr=-1), process top-most first (ascending r)
                    sorted_boxes = sorted(list(boxes_to_move), key=lambda x: x[0], reverse=(dr > 0))
                    
                    # Clear old positions first (safe because we have the list)
                    # Actually, if we clear them all first, we are safe.
                    # But we must be careful not to clear something we just wrote if we did it sequentially.
                    # Standard approach: Read all, Clear all, Write all.
                    
                    # 1. Clear
                    for br, bc in sorted_boxes:
                        grid[br][bc] = '.'
                        grid[br][bc+1] = '.'
                    
                    # 2. Write new
                    for br, bc in sorted_boxes:
                        grid[br+dr][bc] = '['
                        grid[br+dr][bc+1] = ']'
                        
                    # Move robot
                    grid[nr][nc] = '@'
                    grid[r][c] = '.'
                    r, c = nr, nc

    return grid

def calculate_gps_sum_part2(grid):
    total = 0
    for r, row in enumerate(grid):
        for c, val in enumerate(row):
            if val == '[':
                total += 100 * r + c
    return total

def print_grid(grid):
    for row in grid:
        print("".join(row))

def solve():
    # Small Example Test
    small_map = """########
#..O.O.#
##@.O..#
#...O..#
#.#.O..#
#...O..#
#......#"""
    small_moves = "<^^>>>vv<v>>v<<"
    
    # Run small example
    print("--- Part 1: Small Example ---")
    grid = parse_map_string(small_map)
    grid = move_robot(grid, small_moves)
    score = calculate_gps_sum(grid)
    print(f"Small Example Score: {score}")
    assert score == 2028, f"Expected 2028, got {score}"

    # Large Example Test
    large_map = """##########
#..O..O.O#
#......O.#
#.OO..O.O#
#..O@..O.#
#O#..O...#
#O..O..O.#
#.OO.O.OO#
#....O...#
##########"""
    large_moves = """<vv>^<v^>v>^vv^v>v<>v^v<v<^vv<<<^><<><>>v<vvv<>^v^>^<<<><<v<<<v^vv^v>^
vvv<<^>^v^^><<>>><>^<<><^vv^^<>vvv<>><^^v>^>vv<>v<<<<v<^v>^<^^>>>^<v<v
><>vv>v^v^<>><>>>><^^>vv>v<^^^>>v^v^<^^>v^^>v^<^v>v<>>v^v^<v>v^^<^^vv<
<<v<^>>^^^^>>>v^<>vvv^><v<<<>^^^vv^<vvv>^>v<^^^^v<>^>vvvv><>>v^<<^^^^^
^><^><>>><>^^<<^^v>>><^<v>^<vv>>v>>>^v><>^v><<<<v>>v<v<v>vvv>^<><<>^><
^>><>^v<><^vvv<^^<><v<<<<<><^v<<<><<<^^<v<^^^><^>>^<v^><<<^>>^v<v^v<v^
>^>>^v>vv>^<<^v<>><<><<v<<v><>v<^vv<<<>^^v^>^^>>><<^v>>v^v><^^>>^<>vv^
<><^^>^^^<><vvvvv^v<v<<>^v<v>v<<^><<><<><<<^^<<<^<<>><<><^^^>^^<>^>v<>
^^>vv<^v^v<vv>^<><v<^v>^^^>>>^^vvv^>vvv<>>>^<^>>>>>^<<^v>^vvv<>^<><<v>
v^^>>><<^^<>>^v^<v^vv<>v^<<>^<^v^v><^<<<><<^<v><v<>vv>>v><v^<vv<>v^<<^"""
    
    # Run large example Part 1
    print("\n--- Part 1: Large Example ---")
    grid = parse_map_string(large_map)
    moves = large_moves.replace('\n', '')
    grid_p1 = [row[:] for row in grid] # Copy for Part 1 logic if needed, but move_robot mutates
    grid = move_robot(grid, moves)
    score = calculate_gps_sum(grid)
    print(f"Large Example Score: {score}")
    assert score == 10092, f"Expected 10092, got {score}"

    # Real Input Part 1
    print("\n--- Part 1: Real Input ---")
    grid, moves = parse_input('input-day15.txt')
    grid_copy = [row[:] for row in grid] # Keep copy for Part 2
    grid = move_robot(grid, moves)
    score = calculate_gps_sum(grid)
    print(f"Part 1 Score: {score}")
    
    # Part 2 Scaled Example
    print("\n--- Part 2: Scaled Example ---")
    grid = parse_map_string(large_map)
    grid = scale_map(grid)
    moves = large_moves.replace('\n', '')
    grid = move_robot_part2(grid, moves)
    score = calculate_gps_sum_part2(grid)
    print(f"Scaled Example Score: {score}")
    assert score == 9021, f"Expected 9021, got {score}"
    
    # Part 2 Real Input
    print("\n--- Part 2: Real Input ---")
    grid, moves = parse_input('input-day15.txt')
    grid = scale_map(grid) # Scale the original input
    grid = move_robot_part2(grid, moves)
    score = calculate_gps_sum_part2(grid)
    print(f"Part 2 Score: {score}")

if __name__ == '__main__':
    solve()
