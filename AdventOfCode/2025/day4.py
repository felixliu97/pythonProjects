import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        return lines
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

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

def count_removed_rolls(grid_input):
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

def run_tests():
    print("Running tests...")
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
    
    print("Verifying Part 1 Example...")
    expected_p1 = 13
    result_p1 = count_accessible_rolls(example_input)
    if result_p1 == expected_p1:
        print(f"✅ Part 1 Passed")
    else:
        print(f"❌ Part 1 Failed: Expected {expected_p1}, Got {result_p1}")
    
    print("Verifying Part 2 Example...")
    expected_p2 = 43
    result_p2 = count_removed_rolls(example_input)
    if result_p2 == expected_p2:
        print(f"✅ Part 2 Passed")
    else:
        print(f"❌ Part 2 Failed: Expected {expected_p2}, Got {result_p2}")
        
    print("✅ Tests completed!")

def solve_part1():
    print("--- Part 1 ---")
    lines = parse_input('input-day4.txt')
    result_p1 = count_accessible_rolls(lines)
    print(f"Result: {result_p1}")

def solve_part2():
    print("--- Part 2 ---")
    lines = parse_input('input-day4.txt')
    result_p2 = count_removed_rolls(lines)
    print(f"Result: {result_p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
