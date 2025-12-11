import sys
from collections import deque

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            grid = []
            for line in f.readlines():
                row = []
                for char in line.strip():
                    if char.isdigit():
                        row.append(int(char))
                    else:
                        row.append(-1)
                grid.append(row)
        return grid
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def run_tests():
    print("Running tests...")
    
    example_input = [
        "89010123",
        "78121874",
        "87430965",
        "96549874",
        "45678903",
        "32019012",
        "01329801",
        "10456732"
    ]
    
    grid = []
    for line in example_input:
        grid.append([int(c) if c != '.' else -1 for c in line])
        
    p1, p2 = solve_logic(grid)
    
    print(f"Test Part 1: {p1}")
    expected_p1 = 36
    if p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1}")
    
    print(f"Test Part 2: {p2}")
    expected_p2 = 81
    if p2 == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {p2}")

    print("✅ Tests completed!")

def get_score(grid, start_r, start_c):
    rows = len(grid)
    cols = len(grid[0])
    queue = deque([(start_r, start_c)])
    visited = set([(start_r, start_c)])
    peaks = set()
    
    while queue:
        r, c = queue.popleft()
        
        if grid[r][c] == 9:
            peaks.add((r, c))
            continue
            
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            
            if 0 <= nr < rows and 0 <= nc < cols:
                if (nr, nc) not in visited:
                    if grid[nr][nc] == grid[r][c] + 1:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
                        
    return len(peaks)

def get_rating(grid, r, c, memo):
    if (r, c) in memo:
        return memo[(r, c)]
    
    if grid[r][c] == 9:
        return 1
    
    rows = len(grid)
    cols = len(grid[0])
    total = 0
    
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        
        if 0 <= nr < rows and 0 <= nc < cols:
            if grid[nr][nc] == grid[r][c] + 1:
                total += get_rating(grid, nr, nc, memo)
                
    memo[(r, c)] = total
    return total

def solve_logic(grid):
    rows = len(grid)
    cols = len(grid[0])
    total_score = 0
    total_rating = 0
    memo = {} 
    
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 0:
                total_score += get_score(grid, r, c)
                total_rating += get_rating(grid, r, c, memo)
                
    return total_score, total_rating

def solve_part1():
    print("--- Part 1 ---")
    grid = parse_input("input-day10.txt")
    p1, _ = solve_logic(grid)
    print(f"Result: {p1}")

def solve_part2():
    print("--- Part 2 ---")
    grid = parse_input("input-day10.txt")
    _, p2 = solve_logic(grid)
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
