import sys

# Increase recursion depth for Part 2 deep paths
sys.setrecursionlimit(20000)

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            lines = f.read().splitlines()
        return lines
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def solve_part1_logic(grid):
    rows = len(grid)
    cols = len(grid[0])
    
    start_col = -1
    for c, char in enumerate(grid[0]):
        if char == 'S':
            start_col = c
            break
            
    if start_col == -1: return 0
    
    # BFS to find all reachable splitters (handling merges)
    # State: (r, c)
    queue = [(0, start_col)]
    seen = set([(0, start_col)])
    
    splitters_hit = 0
    
    idx = 0
    while idx < len(queue):
        r, c = queue[idx]
        idx += 1
        
        # Check bounds: if out of bounds, beam exits (valid path but no splitter)
        if r >= rows or r < 0 or c >= cols or c < 0:
            continue
            
        char = grid[r][c]
        
        if char == 'S' or char == '.':
            # Move down
            nr, nc = r + 1, c
            if (nr, nc) not in seen:
                seen.add((nr, nc))
                queue.append((nr, nc))
                 
        elif char == '^':
            splitters_hit += 1
            # Split left and right (horizontal)
            # "continues from the immediate left and from the immediate right"
            # Directions: (r, c-1) and (r, c+1)
            
            for nc in [c-1, c+1]:
                nr = r
                if (nr, nc) not in seen:
                    seen.add((nr, nc))
                    queue.append((nr, nc))
                    
    return splitters_hit

def solve_part2_logic(grid):
    # DFS Counting paths (timelines)
    rows = len(grid)
    cols = len(grid[0])
    
    start_col = -1
    for c, char in enumerate(grid[0]):
        if char == 'S':
            start_col = c
            break
            
    memo = {}
    visiting = set()
    
    def count_paths(r, c):
        # If out of bounds or bottom, it's 1 timeline completion
        if r >= rows or r < 0 or c >= cols or c < 0:
            return 1
            
        state = (r, c)
        if state in memo: return memo[state]
        if state in visiting:
            # Cycle detected. Treat as 0 paths (non-terminating)
            return 0
        
        visiting.add(state)
        
        char = grid[r][c]
        res = 0
        
        if char == 'S' or char == '.':
            res = count_paths(r + 1, c)
        elif char == '^':
            res = count_paths(r, c - 1) + count_paths(r, c + 1)
            
        visiting.remove(state)
        memo[state] = res
        return res

    return count_paths(0, start_col)

def run_tests():
    print("Running tests...")
    
    example_input = """
.......S.......
...............
.......^.......
...............
......^.^......
...............
.....^.^.^.....
...............
....^.^...^....
...............
...^.^...^.^...
...............
..^...^.....^..
...............
.^.^.^.^.^...^.
...............
"""
    grid = [line for line in example_input.splitlines() if line.strip()]
    
    print("Verifying Part 1 Example...")
    p1 = solve_part1_logic(grid)
    expected_p1 = 21
    if p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1}")
        
    print("Verifying Part 2 Example...")
    p2 = solve_part2_logic(grid)
    expected_p2 = 40
    if p2 == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {p2}")

    print("✅ Tests completed!")

def solve_part1():
    print("--- Part 1 ---")
    grid = parse_input('2025-day7.txt')
    result = solve_part1_logic(grid)
    print(f"Result: {result}")

def solve_part2():
    print("--- Part 2 ---")
    grid = parse_input('2025-day7.txt')
    result = solve_part2_logic(grid)
    print(f"Result: {result}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
