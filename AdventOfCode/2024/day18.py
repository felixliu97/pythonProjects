from collections import deque

def parse_input(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    coords = []
    for line in lines:
        if line.strip():
            x, y = map(int, line.strip().split(','))
            coords.append((x, y))
    return coords

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
    
    # We want to find the first index 'i' such that coords[:i+1] blocks the path.
    # This means path exists for coords[:i] but NOT for coords[:i+1].
    
    # Invariant: path is possible at 'low' (actually we need to be careful with range)
    # Let's search for the *first failing* index.
    
    # Boundary check: If 0 blocks it? Or if all preserve it?
    # We assume it eventually gets blocked.
    
    # If mid is blocked, answer is <= mid.
    # If mid is open, answer is > mid.
    
    result_idx = -1
    
    while low <= high:
        mid = (low + high) // 2
        
        # Check if path exists with bytes 0..mid (inclusive count is mid+1)
        # Using subset
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

def solve():
    # Example Verification
    # Grid 0-6 (size 6), 12 bytes
    example_coords = [
        (5,4), (4,2), (4,5), (3,0), (2,1), (6,3),
        (2,4), (1,5), (0,6), (3,3), (2,6), (5,1),
        (1,2), (5,5), (2,5), (6,5), (1,4), (0,4),
        (6,4), (1,1), (6,1), (1,0), (0,5), (1,6), (2,0)
    ]
    # Take first 12
    ex_12 = example_coords[:12]
    dist = shortest_path(6, ex_12)
    print(f"Example (Grid 6, 12 bytes): {dist}")
    assert dist == 22, f"Expected 22, got {dist}"
    
    # Part 2 Example
    cutoff = find_cutoff_byte(6, example_coords)
    print(f"Example Cutoff: {cutoff}")
    assert cutoff == (6,1), f"Expected (6,1), got {cutoff}"

    # Real Input
    # Grid 0-70 (size 70), 1024 bytes
    all_coords = parse_input('input-day18.txt')
    first_1024 = all_coords[:1024]
    
    dist = shortest_path(70, first_1024)
    print(f"Part 1 (Grid 70, 1024 bytes): {dist}")
    
    # Part 2 Real
    cutoff = find_cutoff_byte(70, all_coords)
    if cutoff:
        print(f"Part 2 Cutoff: {cutoff[0]},{cutoff[1]}")
    else:
        print("Part 2: No cutoff found!")

if __name__ == '__main__':
    solve()
