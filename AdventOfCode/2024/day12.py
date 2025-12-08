from collections import deque

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            grid = [line.strip() for line in f.readlines()]
        return grid
    except FileNotFoundError:
        print(f"Error: File {filename} not found.")
        return []

def count_corners(grid, r, c):
    rows = len(grid)
    cols = len(grid[0])
    plant_type = grid[r][c]
    corners = 0
    
    def match(nr, nc):
        if 0 <= nr < rows and 0 <= nc < cols:
            return grid[nr][nc] == plant_type
        return False

    # Directions
    n = match(r - 1, c)
    s = match(r + 1, c)
    w = match(r, c - 1)
    e = match(r, c + 1)
    
    nw = match(r - 1, c - 1)
    ne = match(r - 1, c + 1)
    sw = match(r + 1, c - 1)
    se = match(r + 1, c + 1)
    
    # Outer corners (Convex)
    if not n and not w: corners += 1
    if not n and not e: corners += 1
    if not s and not w: corners += 1
    if not s and not e: corners += 1
    
    # Inner corners (Concave)
    if n and w and not nw: corners += 1
    if n and e and not ne: corners += 1
    if s and w and not sw: corners += 1
    if s and e and not se: corners += 1
    
    return corners

def solve(filename):
    grid = parse_input(filename)
    if not grid:
        return 0, 0
    
    rows = len(grid)
    cols = len(grid[0])
    visited = set()
    total_price_p1 = 0
    total_price_p2 = 0
    
    for r in range(rows):
        for c in range(cols):
            if (r, c) not in visited:
                # Start new region
                plant_type = grid[r][c]
                area = 0
                perimeter = 0
                sides = 0 # equivalent to corners
                
                queue = deque([(r, c)])
                visited.add((r, c))
                
                while queue:
                    curr_r, curr_c = queue.popleft()
                    area += 1
                    
                    # Count corners for Part 2
                    sides += count_corners(grid, curr_r, curr_c)
                    
                    # Check neighbors for Part 1 perimeter and traversal
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = curr_r + dr, curr_c + dc
                        
                        if 0 <= nr < rows and 0 <= nc < cols:
                            if grid[nr][nc] == plant_type:
                                if (nr, nc) not in visited:
                                    visited.add((nr, nc))
                                    queue.append((nr, nc))
                            else:
                                perimeter += 1
                        else:
                            perimeter += 1
                            
                total_price_p1 += area * perimeter
                total_price_p2 += area * sides
                
    return total_price_p1, total_price_p2

def test():
    # Helper to run test on simple grid strings
    def verify(grid_str_list, expected_p1, expected_p2):
        # Create temporary file or just modify solve to accept list?
        # Let's modify solve to accept grid directly for testing, or just copy-paste logic
        # For simplicity, implementing mini-solver here
        grid = grid_str_list
        rows = len(grid)
        cols = len(grid[0])
        visited = set()
        p1 = 0
        p2 = 0
        for r in range(rows):
            for c in range(cols):
                if (r, c) not in visited:
                    plant_type = grid[r][c]
                    area = 0
                    perim = 0
                    sides = 0
                    q = deque([(r,c)])
                    visited.add((r,c))
                    while q:
                        cr, cc = q.popleft()
                        area += 1
                        sides += count_corners(grid, cr, cc)
                        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                            nr, nc = cr+dr, cc+dc
                            if 0 <= nr < rows and 0 <= nc < cols:
                                if grid[nr][nc] == plant_type:
                                    if (nr, nc) not in visited:
                                        visited.add((nr, nc))
                                        q.append((nr, nc))
                                else:
                                    perim += 1
                            else:
                                perim += 1
                    p1 += area * perim
                    p2 += area * sides
        
        print(f"Test P1: {p1} (Exp: {expected_p1}) | P2: {p2} (Exp: {expected_p2})")
        if expected_p1 is not None: assert p1 == expected_p1
        if expected_p2 is not None: assert p2 == expected_p2

    print("--- Test Case 1 ---")
    verify([
        "AAAA",
        "BBCD",
        "BBCC",
        "EEEC"
    ], 140, 80)

    print("--- Test Case 2 ---")
    verify([
        "OOOOO",
        "OXOXO",
        "OOOOO",
        "OXOXO",
        "OOOOO"
    ], 772, 436)
    
    print("--- Test Case 3 ---")
    verify([
        "EEEEE",
        "EXXXX",
        "EEEEE",
        "EXXXX",
        "EEEEE"
    ], None, 236)

    print("--- Test Case 4 ---")
    verify([
        "AAAAAA",
        "AAABBA",
        "AAABBA",
        "ABBAAA",
        "ABBAAA",
        "AAAAAA"
    ], None, 368)

    print("--- Test Case 5 (Large) ---")
    verify([
        "RRRRIICCFF",
        "RRRRIICCCF",
        "VVRRRCCFFF",
        "VVRCCCJFFF",
        "VVVVCJJCFE",
        "VVIVCCJJEE",
        "VVIIICJJEE",
        "MIIIIIJJEE",
        "MIIISIJEEE",
        "MMMISSJEEE"
    ], 1930, 1206)

if __name__ == "__main__":
    test()
    print("Tests passed!")
    p1, p2 = solve("input-day12.txt")
    print(f"Part 1 Result: {p1}")
    print(f"Part 2 Result: {p2}")
