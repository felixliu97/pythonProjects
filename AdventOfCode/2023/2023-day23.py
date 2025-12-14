import sys
from collections import deque

sys.setrecursionlimit(1000000)

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def build_graph(grid, start, end, part2=False):
    rows = len(grid)
    cols = len(grid[0])
    
    # Identify key nodes: Start, End, and Junctions (neighbors > 2)
    nodes = {start, end}
    
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '#': continue
            neighbors = 0
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != '#':
                    neighbors += 1
            if neighbors > 2:
                nodes.add((r, c))
                
    # Build Adjacency List for Key Nodes
    # BFS from each node to reachable nodes
    graph = {node: {} for node in nodes}
    
    for r, c in nodes:
        q = [(0, r, c)]
        visited = {(r, c)}
        
        while q:
            dist, curr_r, curr_c = q.pop(0)
            
            if dist > 0 and (curr_r, curr_c) in nodes:
                graph[(r, c)][(curr_r, curr_c)] = dist
                continue
            
            # Explore neighbors
            dirs = []
            if part2:
                dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            else:
                tile = grid[curr_r][curr_c]
                if tile == '>': dirs = [(0, 1)]
                elif tile == '<': dirs = [(0, -1)]
                elif tile == 'v': dirs = [(1, 0)]
                elif tile == '^': dirs = [(-1, 0)]
                else: dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            
            for dr, dc in dirs:
                nr, nc = curr_r + dr, curr_c + dc
                
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != '#':
                    if (nr, nc) not in visited:
                        visited.add((nr, nc))
                        q.append((dist + 1, nr, nc))
    
    # print(f"Graph built (P2={part2}). Nodes: {len(graph)}. Start: {start}, End: {end}", flush=True)
    # for n, edges in graph.items():
    #     print(f"  {n}: {edges}", flush=True)
                        
    return graph

def longest_path_fast(adj, current, end, visited):
    if current == end:
        return 0
    
    max_len = -1
    
    for neighbor, weight in adj[current]:
        if not (visited & (1 << neighbor)):
            res = longest_path_fast(adj, neighbor, end, visited | (1 << neighbor))
            if res != -1:
                if weight + res > max_len:
                    max_len = weight + res
    return max_len

def solve(data):
    grid = data.split('\n')
    rows = len(grid)
    cols = len(grid[0])
    
    start = (0, 1)
    end = (rows - 1, cols - 2)
    
    for c in range(cols):
        if grid[0][c] == '.':
            start = (0, c)
            break
            
    for c in range(cols):
        if grid[rows-1][c] == '.':
            end = (rows-1, c)
            break
            
    def solve_graph(graph):
        nodes = list(graph.keys())
        node_to_id = {node: i for i, node in enumerate(nodes)}
        
        start_id = node_to_id[start]
        end_id = node_to_id[end]
        
        adj = [[] for _ in range(len(nodes))]
        for u, neighbors in graph.items():
            u_id = node_to_id[u]
            for v, dist in neighbors.items():
                v_id = node_to_id[v]
                adj[u_id].append((v_id, dist))
                
        return longest_path_fast(adj, start_id, end_id, 1 << start_id)

    # Part 1: Directed
    graph1 = build_graph(grid, start, end, part2=False)
    p1 = solve_graph(graph1)
    
    # Part 2: Undirected
    graph2 = build_graph(grid, start, end, part2=True)
    p2 = solve_graph(graph2)
    
    return p1, p2

def run_tests():
    print("Running tests...")
    example = """#.#####################
#.......#########...###
#######.#########.#.###
###.....#.>.>.###.#.###
###v#####.#v#.###.#.###
###.>...#.#.#.....#...#
###v###.#.#.#########.#
###...#.#.#.......#...#
#####.#.#.#######.#.###
#.....#.#.#.......#...#
#.#####.#.#.#########v#
#.#...#...#...###...>.#
#.#.#v#######v###.###v#
#...#.>.#...>.>.#.###.#
#####v#.#.###v#.#.###.#
#.....#...#...#.#.#...#
#.#########.###.#.#.###
#...###...#...#...#.###
###.###.#.###v#####v###
#...#...#.#.>.>.#.>.###
#.###.###.#.###.#.#v###
#.....###...###...#...#
#####################.#"""
    
    p1, p2 = solve(example)
    expected_p1 = 94
    expected_p2 = 154
    
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
    data = parse_input("2023-day23.txt")
    p1, p2 = solve(data)
    print("--- Part 1 ---")
    print(f"Result: {p1}")
    print("--- Part 2 ---")
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1_and_2()
