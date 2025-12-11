import sys
from collections import deque

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            grid = [line.strip() for line in f.readlines()]
        return grid
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def run_tests():
    print("Running tests...")
    
    # Test Case 1
    grid1 = [
        "AAAA",
        "BBCD",
        "BBCC",
        "EEEC"
    ]
    p1, p2 = solve_logic(grid1)
    if p1 == 140: print("✅ Test 1 P1 Passed")
    else: print(f"❌ Test 1 P1 Failed: Exp 140, Got {p1}")
    if p2 == 80: print("✅ Test 1 P2 Passed")
    else: print(f"❌ Test 1 P2 Failed: Exp 80, Got {p2}")
    
    # Test Case 2
    grid2 = [
        "OOOOO",
        "OXOXO",
        "OOOOO",
        "OXOXO",
        "OOOOO"
    ]
    p1, p2 = solve_logic(grid2)
    if p1 == 772: print("✅ Test 2 P1 Passed")
    else: print(f"❌ Test 2 P1 Failed: Exp 772, Got {p1}")
    if p2 == 436: print("✅ Test 2 P2 Passed")
    else: print(f"❌ Test 2 P2 Failed: Exp 436, Got {p2}")

    # Test Case 3
    grid3 = [
        "EEEEE",
        "EXXXX",
        "EEEEE",
        "EXXXX",
        "EEEEE"
    ]
    _, p2 = solve_logic(grid3)
    if p2 == 236: print("✅ Test 3 P2 Passed")
    else: print(f"❌ Test 3 P2 Failed: Exp 236, Got {p2}")

    # Test Case 4
    grid4 = [
        "AAAAAA",
        "AAABBA",
        "AAABBA",
        "ABBAAA",
        "ABBAAA",
        "AAAAAA"
    ]
    _, p2 = solve_logic(grid4)
    if p2 == 368: print("✅ Test 4 P2 Passed")
    else: print(f"❌ Test 4 P2 Failed: Exp 368, Got {p2}")

    # Test Case 5 (Large)
    grid5 = [
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
    ]
    p1, p2 = solve_logic(grid5)
    if p1 == 1930: print("✅ Test 5 P1 Passed")
    else: print(f"❌ Test 5 P1 Failed: Exp 1930, Got {p1}")
    if p2 == 1206: print("✅ Test 5 P2 Passed")
    else: print(f"❌ Test 5 P2 Failed: Exp 1206, Got {p2}")

    print("✅ Tests completed!")

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

def solve_logic(grid):
    rows = len(grid)
    cols = len(grid[0])
    visited = set()
    total_price_p1 = 0
    total_price_p2 = 0
    
    for r in range(rows):
        for c in range(cols):
            if (r, c) not in visited:
                plant_type = grid[r][c]
                area = 0
                perimeter = 0
                sides = 0 
                
                queue = deque([(r, c)])
                visited.add((r, c))
                
                while queue:
                    curr_r, curr_c = queue.popleft()
                    area += 1
                    
                    sides += count_corners(grid, curr_r, curr_c)
                    
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

def solve_part1():
    print("--- Part 1 ---")
    grid = parse_input("input-day12.txt")
    p1, _ = solve_logic(grid)
    print(f"Result: {p1}")

def solve_part2():
    print("--- Part 2 ---")
    grid = parse_input("input-day12.txt")
    _, p2 = solve_logic(grid)
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
