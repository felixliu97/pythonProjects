import sys
from collections import defaultdict, deque
import random

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def build_graph(data):
    adj = defaultdict(set)
    edges = []
    
    for line in data.split('\n'):
        src, dsts_str = line.split(': ')
        dsts = dsts_str.split(' ')
        for dst in dsts:
            adj[src].add(dst)
            adj[dst].add(src)
            edges.append(tuple(sorted((src, dst))))
            
    return adj, list(set(edges))

def bfs(adj, start, end):
    # Find shortest path
    q = deque([start])
    parent = {start: None}
    
    while q:
        curr = q.popleft()
        if curr == end:
            break
        for neighbor in adj[curr]:
            if neighbor not in parent:
                parent[neighbor] = curr
                q.append(neighbor)
                
    if end not in parent:
        return None
        
    path = []
    curr = end
    while curr != start:
        prev = parent[curr]
        path.append(tuple(sorted((prev, curr))))
        curr = prev
    return path

def solve(data):
    adj, all_edges = build_graph(data)
    nodes = list(adj.keys())
    
    # Statistical Approach needs to be robust
    max_attempts = 100
    
    for attempt in range(max_attempts):
        # Run BFS between random pairs
        edge_counts = defaultdict(int)
        
        # More samples per attempt
        for _ in range(500):
            src = random.choice(nodes)
            dst = random.choice(nodes)
            if src == dst: continue
            
            path = bfs(adj, src, dst)
            if path:
                for edge in path:
                    edge_counts[edge] += 1
                    
        sorted_edges = sorted(edge_counts.items(), key=lambda x: x[1], reverse=True)
        top_edges = [e[0] for e in sorted_edges[:3]]
        
        # print(f"Attempt {attempt+1} candidates: {top_edges}", flush=True)
        
        # Remove them
        temp_adj = defaultdict(set)
        for u, neighbors in adj.items():
            temp_adj[u] = neighbors.copy()
            
        for u, v in top_edges:
            if v in temp_adj[u]: temp_adj[u].remove(v)
            if u in temp_adj[v]: temp_adj[v].remove(u)
            
        # Count components
        components = []
        visited = set()
        
        for node in nodes:
            if node not in visited:
                comp_size = 0
                q = deque([node])
                visited.add(node)
                comp_size += 1
                
                while q:
                    curr = q.popleft()
                    for neighbor in temp_adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            comp_size += 1
                            q.append(neighbor)
                components.append(comp_size)
                
        if len(components) == 2:
            return components[0] * components[1]
    
    return None

def run_tests():
    print("Running tests...")
    example = """jqt: rhn xhk nvd
rsh: frs pzl lsr
xhk: hfx
cmg: qnr nvd lhk bvb
rhn: xhk bvb hfx
bvb: xhk hfx
pzl: lsr hfx nvd
qnr: nvd
ntq: jqt hfx bvb xhk
nvd: lhk
lsr: lhk
rzs: qnr cmg lsr rsh
frs: qnr lhk lsr"""
    
    # Retry logic if randomness fails in test?
    # Test example small enough that randomness usually works.
    res = solve(example)
    expected = 54
    
    if res == expected:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected}, Got {res}")
        
    print("✅ Tests completed!")

def solve_part1_and_2():
    data = parse_input("2023-day25.txt")
    res = solve(data)
    print("--- Part 1 ---")
    print(f"Result: {res}")
    print("--- Part 2 ---")
    print("Result: Check Stars")

if __name__ == "__main__":
    run_tests()
    solve_part1_and_2()
