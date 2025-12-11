import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            content = f.read()
            
        parts = content.split('\n\n')
        grid_str = parts[0].strip().split('\n')
        grid = [list(line) for line in grid_str]
        
        moves_str = parts[1].replace('\n', '').strip()
        
        return grid, moves_str
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def run_tests():
    print("Running tests...")
    
    # Small Example Test
    small_map = """########
#..O.O.#
##@.O..#
#...O..#
#.#.O..#
#...O..#
#......#"""
    small_moves = "<^^>>>vv<v>>v<<"
    
    print("--- Part 1: Small Example ---")
    grid = parse_map_string(small_map)
    grid = move_robot(grid, small_moves)
    score = calculate_gps_sum(grid)
    print(f"Small Example Score: {score}")
    expected_small = 2028
    if score == expected_small:
        print("✅ Small Example Passed")
    else:
        print(f"❌ Small Example Failed: Expected {expected_small}, Got {score}")

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
    large_moves_raw = """<vv>^<v^>v>^vv^v>v<>v^v<v<^vv<<<^><<><>>v<vvv<>^v^>^<<<><<v<<<v^vv^v>^
vvv<<^>^v^^><<>>><>^<<><^vv^^<>vvv<>><^^v>^>vv<>v<<<<v<^v>^<^^>>>^<v<v
><>vv>v^v^<>><>>>><^^>vv>v<^^^>>v^v^<^^>v^^>v^<^v>v<>>v^v^<v>v^^<^^vv<
<<v<^>>^^^^>>>v^<>vvv^><v<<<>^^^vv^<vvv>^>v<^^^^v<>^>vvvv><>>v^<<^^^^^
^><^><>>><>^^<<^^v>>><^<v>^<vv>>v>>>^v><>^v><<<<v>>v<v<v>vvv>^<><<>^><
^>><>^v<><^vvv<^^<><v<<<<<><^v<<<><<<^^<v<^^^><^>>^<v^><<<^>>^v<v^v<v^
>^>>^v>vv>^<<^v<>><<><<v<<v><>v<^vv<<<>^^v^>^^>>><<^v>>v^v><^^>>^<>vv^
<><^^>^^^<><vvvvv^v<v<<>^v<v>v<<^><<><<><<<^^<<<^<<>><<><^^^>^^<>^>v<>
^^>vv<^v^v<vv>^<><v<^v>^^^>>>^^vvv^>vvv<>>>^<^>>>>>^<<^v>^vvv<>^<><<v>
v^^>>><<^^<>>^v^<v^vv<>v^<<>^<^v^v><^<<<><<^<v><v<>vv>>v><v^<vv<>v^<<^"""
    large_moves = large_moves_raw.replace('\n', '')

    print("\n--- Part 1: Large Example ---")
    grid = parse_map_string(large_map)
    grid = move_robot(grid, large_moves)
    score = calculate_gps_sum(grid)
    print(f"Large Example Score: {score}")
    expected_large_p1 = 10092
    if score == expected_large_p1:
        print("✅ Large Example P1 Passed")
    else:
        print(f"❌ Large Example P1 Failed: Expected {expected_large_p1}, Got {score}")

    # Part 2 Scaled Example
    print("\n--- Part 2: Scaled Example ---")
    grid = parse_map_string(large_map)
    grid = scale_map(grid)
    grid = move_robot_part2(grid, large_moves)
    score = calculate_gps_sum_part2(grid)
    print(f"Scaled Example Score: {score}")
    expected_large_p2 = 9021
    if score == expected_large_p2:
        print("✅ Large Example P2 Passed")
    else:
        print(f"❌ Large Example P2 Failed: Expected {expected_large_p2}, Got {score}")

    print("✅ Tests completed!")

def find_robot(grid):
    for r, row in enumerate(grid):
        for c, val in enumerate(row):
            if val == '@':
                return r, c
    return None

def parse_map_string(map_str):
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
            cr, cc = nr, nc
            while 0 <= cr < rows and 0 <= cc < cols and grid[cr][cc] == 'O':
                cr += dr
                cc += dc
            
            if not (0 <= cr < rows and 0 <= cc < cols):
                continue

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
            if dr == 0:
                # Horizontal Move
                cr, cc = nr, nc
                while 0 <= cr < rows and 0 <= cc < cols and grid[cr][cc] in ['[', ']']:
                    cc += dc
                
                if not (0 <= cc < cols): continue
                if grid[cr][cc] == '#': continue
                if grid[cr][cc] == '.':
                    curr_c = cc
                    while curr_c != nc:
                        prev_c = curr_c - dc
                        grid[cr][curr_c] = grid[cr][prev_c]
                        curr_c = prev_c
                    
                    grid[nr][nc] = '@'
                    grid[r][c] = '.'
                    r, c = nr, nc
            else:
                # Vertical Move
                boxes_to_move = set()
                queue = []
                
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
                    
                    if not possible:
                        break
                
                if possible:
                    sorted_boxes = sorted(list(boxes_to_move), key=lambda x: x[0], reverse=(dr > 0))
                    
                    for br, bc in sorted_boxes:
                        grid[br][bc] = '.'
                        grid[br][bc+1] = '.'
                    
                    for br, bc in sorted_boxes:
                        grid[br+dr][bc] = '['
                        grid[br+dr][bc+1] = ']'
                        
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

def solve_part1():
    print("--- Part 1 ---")
    grid, moves = parse_input("input-day15.txt")
    grid = move_robot(grid, moves)
    score = calculate_gps_sum(grid)
    print(f"Result: {score}")

def solve_part2():
    print("--- Part 2 ---")
    grid, moves = parse_input("input-day15.txt")
    grid = scale_map(grid)
    grid = move_robot_part2(grid, moves)
    score = calculate_gps_sum_part2(grid)
    print(f"Result: {score}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
