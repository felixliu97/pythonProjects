import sys
from collections import defaultdict

def parse_input(filename):
    points = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 3:
                    points.append(tuple(map(int, parts)))
        return points
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.num_components = n
        self.sizes = {i: 1 for i in range(n)}

    def find(self, i):
        if self.parent[i] != i:
            self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i, j):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            self.parent[root_i] = root_j
            self.sizes[root_j] += self.sizes[root_i]
            del self.sizes[root_i]
            self.num_components -= 1
            return True
        return False

def get_sorted_edges(points):
    n = len(points)
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            p1 = points[i]
            p2 = points[j]
            dist_sq = (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2
            edges.append((dist_sq, i, j))
    edges.sort(key=lambda x: x[0])
    return edges

def solve_part1_logic(points, num_connections=1000):
    n = len(points)
    uf = UnionFind(n)
    edges = get_sorted_edges(points)
    
    limit = min(len(edges), num_connections)
    for k in range(limit):
        _, i, j = edges[k]
        uf.union(i, j)
        
    sizes = sorted(uf.sizes.values(), reverse=True)
    
    if len(sizes) >= 3:
        return sizes[0] * sizes[1] * sizes[2]
    elif sizes:
        # Fallback if product definition requires strictly 3 or just "largest 3"
        # If fewer than 3, multiply what we have
        res = 1
        for s in sizes:
            res *= s
        return res
    return 0

def solve_part2_logic(points):
    n = len(points)
    uf = UnionFind(n)
    edges = get_sorted_edges(points)
    
    last_pair_x_product = 0
    
    for dist_sq, i, j in edges:
        if uf.union(i, j):
            if uf.num_components == 1:
                # This was the connection that united everything
                last_pair_x_product = points[i][0] * points[j][0]
                break
                
    return last_pair_x_product

def run_tests():
    print("Running tests...")
    example_input = """
162,817,812
57,618,57
906,360,560
592,479,940
352,342,300
466,668,158
542,29,236
431,825,988
739,650,466
52,470,668
216,146,977
819,987,18
117,168,530
805,96,715
346,949,466
970,615,88
941,993,340
862,61,35
984,92,344
425,690,689
"""
    points = []
    for line in example_input.strip().splitlines():
        points.append(tuple(map(int, line.split(','))))
        
    print("Verifying Part 1 Example...")
    # Example says 10 shortest connections
    p1 = solve_part1_logic(points, num_connections=10)
    expected_p1 = 40
    if p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1}")
        
    print("Verifying Part 2 Example...")
    p2 = solve_part2_logic(points)
    expected_p2 = 25272
    if p2 == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {p2}")

    print("✅ Tests completed!")

def solve_part1():
    print("--- Part 1 ---")
    points = parse_input('input-day8.txt')
    result = solve_part1_logic(points, num_connections=1000)
    print(f"Result: {result}")

def solve_part2():
    print("--- Part 2 ---")
    points = parse_input('input-day8.txt')
    result = solve_part2_logic(points)
    print(f"Result: {result}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
