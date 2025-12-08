from collections import defaultdict

def parse_input(filename):
    adj = defaultdict(set)
    try:
        with open(filename, 'r') as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split('-')
                    if len(parts) == 2:
                        u, v = parts
                        adj[u].add(v)
                        adj[v].add(u)
    except FileNotFoundError:
        return None
    return adj

def parse_example(example_str):
    adj = defaultdict(set)
    for line in example_str.strip().split('\n'):
        if line.strip():
            parts = line.strip().split('-')
            if len(parts) == 2:
                u, v = parts
                adj[u].add(v)
                adj[v].add(u)
    return adj

def find_triangles(adj):
    triangles = set()
    
    # Iterate over all nodes
    nodes = sorted(list(adj.keys()))
    
    for i in range(len(nodes)):
        u = nodes[i]
        neighbors_u = list(adj[u])
        
        # Check pairs of neighbors
        for j in range(len(neighbors_u)):
            v = neighbors_u[j]
            
            # Optimization: enforce order to avoid duplicates early?
            # Or just check if they are connected and add frozenset
            if v > u: # Enforce u < v
                if v in adj: # Should be
                     for w in adj[v]:
                         if w > v: # Enforce v < w
                             if w in adj[u]:
                                 # Found triangle u-v-w where u < v < w
                                 triangles.add((u, v, w))
                                 
    return triangles

def bron_kerbosch(R, P, X, adj, max_clique):
    if not P and not X:
        if len(R) > len(max_clique[0]):
            max_clique[0] = R
        return

    # Pivot: choose an element u from P U X to minimize branching
    # u = next(iter(P.union(X))) # simple pivot
    # Better pivot: u in P U X that maximizes |P over neighbors(u)|
    
    # Simple pivot is often enough for AoC, but let's try to be slightly safe
    pivot = max(P | X, key=lambda u: len(adj[u] & P))
    
    for v in list(P - adj[pivot]):
        bron_kerbosch(R | {v}, P & adj[v], X & adj[v], adj, max_clique)
        P.remove(v)
        X.add(v)

def find_largest_clique(adj):
    # Bron-Kerbosch with pivoting
    P = set(adj.keys())
    R = set()
    X = set()
    max_clique = [set()]
    
    bron_kerbosch(R, P, X, adj, max_clique)
    return max_clique[0]

def get_password(clique):
    return ",".join(sorted(list(clique)))

def solve():
    # Example
    example_input = """kh-tc
qp-kh
de-cg
ka-co
yn-aq
qp-ub
cg-tb
vc-aq
tb-ka
wh-tc
yn-cg
kh-ub
ta-co
de-co
tc-td
tb-wq
wh-td
ta-ka
td-qp
aq-cg
wq-ub
ub-vc
de-ta
wq-aq
wq-vc
wh-yn
ka-de
kh-ta
co-tc
wh-qp
tb-vc
td-yn"""
    
    adj_ex = parse_example(example_input)
    triangles_ex = find_triangles(adj_ex)
    print(f"Example Triangles Found: {len(triangles_ex)} (Expected 12)")
    assert len(triangles_ex) == 12
    
    t_triangles_ex = [t for t in triangles_ex if any(name.startswith('t') for name in t)]
    print(f"Example 't' Triangles: {len(t_triangles_ex)} (Expected 7)")
    assert len(t_triangles_ex) == 7
    print("Example Part 1 passed!")
    
    # Part 2 Example
    largest_clique_ex = find_largest_clique(adj_ex)
    password_ex = get_password(largest_clique_ex)
    print(f"Example Part 2 Password: {password_ex} (Expected: co,de,ka,ta)")
    assert password_ex == "co,de,ka,ta"
    print("Example Part 2 passed!")

    # Real Input
    adj_real = parse_input('input-day23.txt')
    if adj_real:
        # Part 1
        triangles_real = find_triangles(adj_real)
        t_triangles_real = [t for t in triangles_real if any(name.startswith('t') for name in t)]
        print(f"\nPart 1 Final Count: {len(t_triangles_real)}")
        
        # Part 2
        largest_clique_real = find_largest_clique(adj_real)
        password_real = get_password(largest_clique_real)
        print(f"Part 2 Final Password: {password_real}")
    else:
        print("input-day23.txt not found. Skipping real input run.")

if __name__ == '__main__':
    solve()
