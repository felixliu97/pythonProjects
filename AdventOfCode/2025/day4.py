def count_accessible_rolls(grid):
    rows = len(grid)
    cols = len(grid[0])
    accessible_count = 0

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '@':
                neighbor_rolls = 0
                # Check 8 neighbors
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        
                        nr, nc = r + dr, c + dc
                        
                        if 0 <= nr < rows and 0 <= nc < cols:
                            if grid[nr][nc] == '@':
                                neighbor_rolls += 1
                
                if neighbor_rolls < 4:
                    accessible_count += 1
                    
    return accessible_count

def solve_part2(grid_input):
    # Convert to mutable grid (list of lists)
    grid = [list(row) for row in grid_input]
    rows = len(grid)
    cols = len(grid[0])
    total_removed = 0
    
    while True:
        to_remove = []
        
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == '@':
                    neighbor_rolls = 0
                    # Check 8 neighbors
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            
                            nr, nc = r + dr, c + dc
                            
                            if 0 <= nr < rows and 0 <= nc < cols:
                                if grid[nr][nc] == '@':
                                    neighbor_rolls += 1
                    
                    if neighbor_rolls < 4:
                        to_remove.append((r, c))
        
        if not to_remove:
            break
            
        total_removed += len(to_remove)
        
        # Remove rolls
        for r, c in to_remove:
            grid[r][c] = '.' # Mark as removed (empty space)
            
    return total_removed

def solve():
    try:
        with open('input-day4.txt', 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print("Error: input-day4.txt not found.")
        return

    result_p1 = count_accessible_rolls(lines)
    print(f"Part 1 - Total accessible rolls: {result_p1}")
    
    result_p2 = solve_part2(lines)
    print(f"Part 2 - Total removed rolls: {result_p2}")

def test_example():
    example_input = [
        "..@@.@@@@.",
        "@@@.@.@.@@",
        "@@@@@.@.@@",
        "@.@@@@..@.",
        "@@.@@@@.@@",
        ".@@@@@@@.@",
        ".@.@.@.@@@",
        "@.@@@.@@@@",
        ".@@@@@@@@.",
        "@.@.@@@.@."
    ]
    
    expected_p1 = 13
    result_p1 = count_accessible_rolls(example_input)
    print(f"Test Example Part 1: Expected {expected_p1}, Got {result_p1}, Pass: {result_p1 == expected_p1}")
    
    expected_p2 = 43
    result_p2 = solve_part2(example_input)
    print(f"Test Example Part 2: Expected {expected_p2}, Got {result_p2}, Pass: {result_p2 == expected_p2}")

if __name__ == "__main__":
    print("Running examples...")
    test_example()
    print("\nRunning solution...")
    solve()
