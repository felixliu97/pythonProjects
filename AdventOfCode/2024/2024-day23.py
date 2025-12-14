import sys
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
        print(f"Error: {filename} not found.")
        sys.exit(1)
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

def run_tests():
    print("Running tests...")
    
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
    print(f"Test Example Triangles Found: {len(triangles_ex)} (Exp 12)")
    
    t_triangles_ex = [t for t in triangles_ex if any(name.startswith('t') for name in t)]
    print(f"Test Example 't' Triangles: {len(t_triangles_ex)} (Exp 7)")
    
    expected_p1 = 7
    if len(t_triangles_ex) == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {len(t_triangles_ex)}")
    
    # Part 2 Example
    largest_clique_ex = find_largest_clique(adj_ex)
    password_ex = get_password(largest_clique_ex)
    print(f"Test Example Part 2 Password: {password_ex} (Exp: co,de,ka,ta)")
    
    expected_p2 = "co,de,ka,ta"
    if password_ex == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {password_ex}")
        
    print("✅ Tests completed!")

def find_triangles(adj):
    triangles = set()
    nodes = sorted(list(adj.keys()))
    
    for i in range(len(nodes)):
        u = nodes[i]
        neighbors_u = list(adj[u])
        
        for j in range(len(neighbors_u)):
            v = neighbors_u[j]
            if v > u: 
                if v in adj: 
                     for w in adj[v]:
                         if w > v: 
                             if w in adj[u]:
                                 triangles.add((u, v, w))
                                 
    return triangles

def bron_kerbosch(R, P, X, adj, max_clique):
    if not P and not X:
        if len(R) > len(max_clique[0]):
            max_clique[0] = R
        return

    # Pivot: choose an element u from P U X to minimize branching
    if not (P | X):
        return

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

def solve_part1():
    print("--- Part 1 ---")
    adj_real = parse_input("2024-day23.txt")
    if not adj_real: return
    
    triangles_real = find_triangles(adj_real)
    t_triangles_real = [t for t in triangles_real if any(name.startswith('t') for name in t)]
    print(f"Result: {len(t_triangles_real)}")

def solve_part2():
    print("--- Part 2 ---")
    adj_real = parse_input("2024-day23.txt")
    if not adj_real: return
    
    largest_clique_real = find_largest_clique(adj_real)
    password_real = get_password(largest_clique_real)
    print(f"Result: {password_real}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
