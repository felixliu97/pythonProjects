
import math

def solve():
    """
    Solves Advent of Code 2025 Day 8.
    """
    
    # 1. Parse Input
    points = []
    try:
        with open('input-day8.txt', 'r') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) == 3:
                    points.append(tuple(map(int, parts)))
    except FileNotFoundError:
        print("Error: input-day8.txt not found.")
        return

    n = len(points)
    if n == 0:
        print("No points found.")
        return

    # 2. Calculate Distances
    # We need to find the closes pairs.
    # Store as (distance_sq, index_1, index_2)
    distances = []
    for i in range(n):
        for j in range(i + 1, n):
            p1 = points[i]
            p2 = points[j]
            # Use squared euclidean distance to avoid sqrt calls for sorting
            dist_sq = (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2
            distances.append((dist_sq, i, j))

    # 3. Sort by distance
    distances.sort(key=lambda x: x[0])

    # 4. Connect top 1000 pairs
    parent = list(range(n))
    
    def find(i):
        if parent[i] != i:
            parent[i] = find(parent[i])
        return parent[i]

    def union(i, j):
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j:
            parent[root_i] = root_j
            return True
        return False

    num_pairs_to_connect = 1000
    if len(distances) < num_pairs_to_connect:
        print(f"Warning: Only {len(distances)} pairs available, connecting all of them.")
        num_pairs_to_connect = len(distances)

    for k in range(num_pairs_to_connect):
        _, i, j = distances[k]
        union(i, j)

    # 5. Analyze Circuits
    # Count sizes of each set
    from collections import defaultdict
    set_sizes = defaultdict(int)
    for i in range(n):
        root = find(i)
        set_sizes[root] += 1
    
    # Get all sizes
    sizes = list(set_sizes.values())
    
    # Sort descending
    sizes.sort(reverse=True)
    
    # 6. Result Part 1
    print("--- Part 1 ---")
    if len(sizes) >= 3:
        result = sizes[0] * sizes[1] * sizes[2]
        print(f"Sizes of 3 largest circuits: {sizes[0]}, {sizes[1]}, {sizes[2]}")
        print(f"Product: {result}")
    else:
        print("Fewer than 3 circuits found:", sizes)
        result = 1
        for s in sizes:
            result *= s
        print(f"Product of all {len(sizes)} circuits: {result}")

    # --- Part 2 ---
    print("\n--- Part 2 ---")
    # Reset Union-Find
    parent = list(range(n))
    num_components = n
    
    # We need to define find/union again or reuse, but referencing 'parent' which is local.
    # To keep it clean, let's just make 'parent' mutable or re-define helpers.
    # The previous find/union captured 'parent' from closure. Redefining logic here cleanly.
    
    def find_p2(i, p_arr):
        if p_arr[i] != i:
            p_arr[i] = find_p2(p_arr[i], p_arr)
        return p_arr[i]

    def union_p2(i, j, p_arr):
        root_i = find_p2(i, p_arr)
        root_j = find_p2(j, p_arr)
        if root_i != root_j:
            p_arr[root_i] = root_j
            return True
        return False

    for dist_sq, i, j in distances:
        if union_p2(i, j, parent):
            num_components -= 1
            if num_components == 1:
                # This is the last connection
                p1 = points[i]
                p2 = points[j]
                print(f"Connected last pair: {p1} and {p2}")
                print(f"Distance squared: {dist_sq}")
                result_p2 = p1[0] * p2[0]
                print(f"Product of X coordinates ({p1[0]} * {p2[0]}): {result_p2}")
                break

if __name__ == "__main__":
    solve()
