import sys
from collections import deque

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        coords = []
        for line in lines:
            if line.strip():
                x, y = map(int, line.strip().split(','))
                coords.append((x, y))
        return coords
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def run_tests():
    print("Running tests...")
    
    # Grid 0-6 (size 6), 12 bytes
    example_coords = [
        (5,4), (4,2), (4,5), (3,0), (2,1), (6,3),
        (2,4), (1,5), (0,6), (3,3), (2,6), (5,1),
        (1,2), (5,5), (2,5), (6,5), (1,4), (0,4),
        (6,4), (1,1), (6,1), (1,0), (0,5), (1,6), (2,0)
    ]
    
    # Test Part 1
    ex_12 = example_coords[:12]
    dist = shortest_path(6, ex_12)
    print(f"Test Part 1 (Size 6, 12 bytes): {dist}")
    
    expected_p1 = 22
    if dist == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {dist}")
        
    # Test Part 2
    cutoff = find_cutoff_byte(6, example_coords)
    print(f"Test Part 2 Cutoff: {cutoff}")
    expected_p2 = (6,1)
    if cutoff == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {cutoff}")
        
    print("✅ Tests completed!")

def shortest_path(grid_size, corrupted_coords):
    start = (0, 0)
    end = (grid_size, grid_size)
    
    corrupted_set = set(corrupted_coords)
    
    # BFS
    queue = deque([(0, 0, 0)]) # x, y, dist
    visited = set([(0, 0)])
    
    while queue:
        x, y, dist = queue.popleft()
        
        if (x, y) == end:
            return dist
        
        # Directions: Up, Down, Left, Right
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            
            if 0 <= nx <= grid_size and 0 <= ny <= grid_size:
                if (nx, ny) not in corrupted_set and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny, dist + 1))
                    
    return -1 # No path found

def find_cutoff_byte(grid_size, coords):
    # Binary Search
    low = 0
    high = len(coords) - 1
    
    result_idx = -1
    
    while low <= high:
        mid = (low + high) // 2
        
        current_corrupted = coords[:mid+1]
        dist = shortest_path(grid_size, current_corrupted)
        
        if dist == -1:
            # Blocked. This could be the first one, or earlier.
            result_idx = mid
            high = mid - 1
        else:
            # Open. The blockage is later.
            low = mid + 1
            
    if result_idx != -1:
        return coords[result_idx]
    return None

def solve_part1():
    print("--- Part 1 ---")
    all_coords = parse_input("input-day18.txt")
    if not all_coords: return
    
    # Grid 0-70 (size 70), 1024 bytes
    first_1024 = all_coords[:1024]
    dist = shortest_path(70, first_1024)
    print(f"Result: {dist}")

def solve_part2():
    print("--- Part 2 ---")
    all_coords = parse_input("input-day18.txt")
    if not all_coords: return
    
    cutoff = find_cutoff_byte(70, all_coords)
    if cutoff:
        print(f"Result: {cutoff[0]},{cutoff[1]}")
    else:
        print("Result: No cutoff found")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
