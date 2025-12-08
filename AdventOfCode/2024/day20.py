from collections import deque

def parse_input(filename):
    with open(filename, 'r') as f:
        grid = [list(line.strip()) for line in f if line.strip()]
    return grid

def find_start_end(grid):
    start = None
    end = None
    for r, row in enumerate(grid):
        for c, val in enumerate(row):
            if val == 'S':
                start = (r, c)
            elif val == 'E':
                end = (r, c)
    return start, end

def bfs_distances(grid, start, end):
    rows = len(grid)
    cols = len(grid[0])
    
    # Map: (r, c) -> distance from start
    dists = {start: 0}
    queue = deque([start])
    
    while queue:
        r, c = queue.popleft()
        
        if (r, c) == end:
            continue # Continue to map full path if needed, but for single path it's fine.
            # Actually we want dists for ALL track points.
        
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            
            if 0 <= nr < rows and 0 <= nc < cols:
                if grid[nr][nc] != '#' and (nr, nc) not in dists:
                    dists[(nr, nc)] = dists[(r, c)] + 1
                    queue.append((nr, nc))
                    
    return dists

def solve_cheats(grid, min_saving=100, max_duration=2):
    start, end = find_start_end(grid)
    dists = bfs_distances(grid, start, end)
    
    # Since there is only a single path, every track cell is reachable and has a unique distance.
    # We can iterate over all track cells u, and check all cells v within dist max_duration.
    
    count = 0
    cheat_savings = {} # saving -> count
    
    # Get all track positions sorted by distance (optional, but good for iteration)
    path_nodes = sorted(dists.keys(), key=lambda k: dists[k])
    
    for u in path_nodes:
        r, c = u
        dist_u = dists[u]
        
        # Check potential cheat endpoints v within manhattan distance max_duration
        # Iterate relative offsets for dist <= max_duration
        # To optimize, we can iterate dr from -max_duration to +max_duration
        # and dc based on remaining budget.
        
        for dr in range(-max_duration, max_duration + 1):
            remaining_dist = max_duration - abs(dr)
            for dc in range(-remaining_dist, remaining_dist + 1):
                if (dr == 0 and dc == 0):
                    continue
                
                cheat_len = abs(dr) + abs(dc)
                if cheat_len > max_duration: 
                    # Should be covered by loop range logic but double check
                    continue 

                nr, nc = r + dr, c + dc
                v = (nr, nc)
                
                if v in dists:
                    dist_v = dists[v]
                    # Saving = (dist_v - dist_u) - manhattan(u, v)
                    saving = (dist_v - dist_u) - cheat_len
                    
                    if saving >= min_saving:
                        count += 1
                        if saving not in cheat_savings:
                            cheat_savings[saving] = 0
                        cheat_savings[saving] += 1
                            
    return count, cheat_savings

def solve():
    # Example
    example_map = """###############
#...#...#.....#
#.#.#.#.#.###.#
#S#...#.#.#...#
#######.#.#.###
#######.#.#...#
#######.#.###.#
###..E#...#...#
###.#######.###
#...###...#...#
#.#####.#.###.#
#.#...#.#.#...#
#.#.#.#.#.#.###
#...#...#...###
###############"""
    grid = [list(line.strip()) for line in example_map.strip().split('\n')]
    
    # Verify example counts Part 1
    print("--- Example Part 1 Verification (Duration 2) ---")
    _, savings = solve_cheats(grid, min_saving=1, max_duration=2)
    
    expected_p1 = {
        2: 14, 4: 14, 6: 2, 8: 4, 10: 2, 12: 3, 20: 1, 36: 1, 38: 1, 40: 1, 64: 1
    }
    
    for k, v in sorted(savings.items()):
        if k in expected_p1:
            print(f"Saving {k}: {v} (Expected {expected_p1[k]})")
            assert v == expected_p1[k]
    print("Part 1 Example passed!")

    # Verify example counts Part 2
    print("\n--- Example Part 2 Verification (Duration 20, Saving >= 50) ---")
    _, savings_p2 = solve_cheats(grid, min_saving=50, max_duration=20)
    
    expected_p2 = {
        50: 32, 52: 31, 54: 29, 56: 39, 58: 25, 60: 23, 62: 20, 64: 19, 
        66: 12, 68: 14, 70: 12, 72: 22, 74: 4, 76: 3
    }
    
    saved_ge_50 = 0
    for k, v in sorted(savings_p2.items()):
        if k >= 50:
            saved_ge_50 += v
            if k in expected_p2:
                print(f"Saving {k}: {v} (Expected {expected_p2[k]})")
                assert v == expected_p2[k]
                
    print("Part 2 Example passed!")

    # Real Input
    try:
        grid = parse_input('input-day20.txt')
        
        # Part 1 Real
        count_p1, _ = solve_cheats(grid, min_saving=100, max_duration=2)
        print(f"\nPart 1 (Savings >= 100, Max Duration 2): {count_p1}")
        
        # Part 2 Real
        count_p2, _ = solve_cheats(grid, min_saving=100, max_duration=20)
        print(f"Part 2 (Savings >= 100, Max Duration 20): {count_p2}")
        
    except FileNotFoundError:
        print("input-day20.txt not found. Skipping real input run.")

if __name__ == '__main__':
    solve()
