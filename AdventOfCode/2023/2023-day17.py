import sys
import heapq

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def solve_dijkstra(grid, min_steps, max_steps):
    rows = len(grid)
    cols = len(grid[0])
    
    pq = [(0, 0, 0, 0, 0, 0)]
    visited = {} # maps state to loss
    came_from = {}
    
    end_states = []
    
    while pq:
        loss, r, c, dr, dc, steps = heapq.heappop(pq)
        
        # Check if better path to this state exists?
        # Dijkstra guarantees first visit is best.
        if (r, c, dr, dc, steps) in visited:
            continue
        visited[(r, c, dr, dc, steps)] = loss
        
        if r == rows - 1 and c == cols - 1:
            if steps >= min_steps:
                # Found end
                # Reconstruct
                path = []
                curr = (r, c, dr, dc, steps)
                while curr in came_from:
                    path.append(curr)
                    curr = came_from[curr]
                path.append(curr)
                path.reverse()
                # print(f"Path found with loss {loss}. Path length: {len(path)}", flush=True)
                # for p in path: print(p, flush=True)
                return loss
        
        possible_moves = []
        if (dr, dc) == (0, 0):
             possible_moves = [(0, 1), (1, 0)] 
        else:
            possible_moves.append((-dc, dr))
            possible_moves.append((dc, -dr))
            possible_moves.append((dr, dc))
            
        for ndr, ndc in possible_moves:
            nr, nc = r + ndr, c + ndc
            
            if 0 <= nr < rows and 0 <= nc < cols:
                new_steps = 1
                same_dir = (ndr == dr and ndc == dc)
                
                if same_dir:
                    new_steps = steps + 1
                    
                if new_steps > max_steps:
                    continue
                    
                if (dr, dc) != (0, 0) and not same_dir:
                    if steps < min_steps:
                        continue
                
                new_loss = loss + int(grid[nr][nc])
                new_state = (nr, nc, ndr, ndc, new_steps)
                
                if new_state not in visited:
                    if new_state not in came_from: # Only record first time (shortest path)
                        came_from[new_state] = (r, c, dr, dc, steps)
                        heapq.heappush(pq, (new_loss, nr, nc, ndr, ndc, new_steps))
                    
    return -1

def solve(data):
    grid = data.split('\n')
    
    p1 = solve_dijkstra(grid, min_steps=0, max_steps=3) # Min steps 0 for P1? effectively 1 because we move 1. 0 constraint is ignorable.
    p2 = solve_dijkstra(grid, min_steps=4, max_steps=10)
    
    return p1, p2

def run_tests():
    print("Running tests...")
    example = """2413432311323
3215453535623
3255245654254
3446585845452
4546657867536
1438598798454
4457876987766
3637877979653
4654967986887
4564679986453
1224686865563
2546548887735
4322674655533"""
    
    p1, p2 = solve(example)
    expected_p1 = 102
    expected_p2 = 94
    
    if p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1}")
        
    if p2 == expected_p2:
         print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {p2}")

    print("✅ Tests completed!")

def solve_part1_and_2():
    data = parse_input("2023-day17.txt")
    p1, p2 = solve(data)
    print("--- Part 1 ---")
    print(f"Result: {p1}")
    print("--- Part 2 ---")
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1_and_2()
