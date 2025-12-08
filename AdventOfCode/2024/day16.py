import heapq
from collections import defaultdict, deque

def parse_input(filename):
    with open(filename, 'r') as f:
        return [list(line.strip()) for line in f if line.strip()]

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

def solve_maze(grid):
    start, end = find_start_end(grid)
    if not start or not end:
        raise ValueError("Start or End not found")

    rows = len(grid)
    cols = len(grid[0])

    # Priority Queue: (cost, r, c, dr, dc)
    # Start facing East: dr=0, dc=1
    start_state = (start[0], start[1], 0, 1)
    pq = [(0, *start_state)]
    
    # Maps for Part 2
    min_cost = defaultdict(lambda: float('inf'))
    min_cost[start_state] = 0
    predecessors = defaultdict(list) # state -> list of prev_states

    best_end_cost = float('inf')
    end_states = []

    while pq:
        cost, r, c, dr, dc = heapq.heappop(pq)

        if cost > min_cost[(r, c, dr, dc)]:
            continue
        
        # Optimization: if we already found a path to end cheaper than this state, optimization
        # But we need ALL best paths, so we can't prune strictly unless cost > best_end_cost
        if cost > best_end_cost:
            continue

        if (r, c) == end:
            if cost < best_end_cost:
                best_end_cost = cost
                end_states = [(r, c, dr, dc)]
            elif cost == best_end_cost:
                end_states.append((r, c, dr, dc))
            continue

        # Possible moves
        moves = []
        
        # 1. Forward
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != '#':
            moves.append((cost + 1, nr, nc, dr, dc))
        
        # 2. Rotate CW
        moves.append((cost + 1000, r, c, dc, -dr))
        
        # 3. Rotate CCW
        moves.append((cost + 1000, r, c, -dc, dr))

        for new_cost, nr, nc, ndr, ndc in moves:
            next_state = (nr, nc, ndr, ndc)
            if new_cost < min_cost[next_state]:
                min_cost[next_state] = new_cost
                predecessors[next_state] = [(r, c, dr, dc)]
                heapq.heappush(pq, (new_cost, *next_state))
            elif new_cost == min_cost[next_state]:
                predecessors[next_state].append((r, c, dr, dc))

    # Part 2: Backtrack
    visited_states = set()
    queue = deque(end_states)
    while queue:
        state = queue.popleft()
        if state in visited_states:
            continue
        visited_states.add(state)
        
        for prev in predecessors[state]:
            queue.append(prev)
            
    unique_tiles = set()
    for r, c, dr, dc in visited_states:
        unique_tiles.add((r, c))
        
    return best_end_cost, len(unique_tiles)

def solve():
    # Small Example 1
    example1_map = """###############
#.......#....E#
#.#.###.#.###.#
#.....#.#...#.#
#.###.#####.#.#
#.#.#.......#.#
#.#.#####.###.#
#...........#.#
###.#.#####.#.#
#...#.....#.#.#
#.#.#.###.#.#.#
#.....#...#.#.#
#.###.#.#.#.#.#
#S..#.....#...#
###############"""
    grid = [list(line.strip()) for line in example1_map.strip().split('\n')]
    score, tiles = solve_maze(grid)
    print(f"Example 1 Score: {score}, Tiles: {tiles}")
    assert score == 7036, f"Expected 7036, got {score}"
    assert tiles == 45, f"Expected 45, got {tiles}"

    # Small Example 2
    example2_map = """#################
#...#...#...#..E#
#.#.#.#.#.#.#.#.#
#.#.#.#...#...#.#
#.#.#.#.###.#.#.#
#...#.#.#.....#.#
#.#.#.#.#.#####.#
#.#...#.#.#.....#
#.#.#####.#.###.#
#.#.#.......#...#
#.#.###.#####.###
#.#.#...#.....#.#
#.#.#.#####.###.#
#.#.#.........#.#
#.#.#.#########.#
#S#.............#
#################"""
    grid = [list(line.strip()) for line in example2_map.strip().split('\n')]
    score, tiles = solve_maze(grid)
    print(f"Example 2 Score: {score}, Tiles: {tiles}")
    assert score == 11048, f"Expected 11048, got {score}"
    assert tiles == 64, f"Expected 64, got {tiles}"

    # Real Input
    grid = parse_input('input-day16.txt')
    score, tiles = solve_maze(grid)
    print(f"Part 1 Score: {score}")
    print(f"Part 2 Tiles: {tiles}")

if __name__ == '__main__':
    solve()
