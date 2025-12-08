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
                        row.append(-1) # Handle potential impassable dots if any
                grid.append(row)
        return grid
    except FileNotFoundError:
        print(f"Error: File {filename} not found.")
        return []

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

def solve(filename):
    grid = parse_input(filename)
    if not grid:
        return 0, 0
        
    rows = len(grid)
    cols = len(grid[0])
    total_score = 0
    total_rating = 0
    
    # Memoization cache for Part 2
    # Though it depends on the path, wait.
    # Actually, since it's a DAG (strictly increasing), the number of paths from (r,c) to any 9
    # is independent of how we got to (r,c). So global memoization works.
    memo = {} 
    
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 0:
                total_score += get_score(grid, r, c)
                total_rating += get_rating(grid, r, c, memo)
                
    return total_score, total_rating

def test():
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
                
    print(f"Test Part 1: {total_score}")
    assert total_score == 36, f"Expected 36, got {total_score}"
    
    print(f"Test Part 2: {total_rating}")
    assert total_rating == 81, f"Expected 81, got {total_rating}"

if __name__ == "__main__":
    test()
    print("Tests passed!")
    p1, p2 = solve("input-day10.txt")
    print(f"Part 1 Result: {p1}")
    print(f"Part 2 Result: {p2}")
