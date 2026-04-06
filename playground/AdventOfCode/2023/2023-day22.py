import sys
from collections import deque, defaultdict
import copy

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def intersect(b1, b2):
    # Check xy intersection
    # b: (x1, y1, z1, x2, y2, z2)
    # Range overlap
    return max(b1[0], b2[0]) <= min(b1[3], b2[3]) and max(b1[1], b2[1]) <= min(b1[4], b2[4])

def solve(data):
    lines = data.split('\n')
    bricks = []
    
    for i, line in enumerate(lines):
        start, end = line.split('~')
        x1, y1, z1 = map(int, start.split(','))
        x2, y2, z2 = map(int, end.split(','))
        # Ensure ordered
        bricks.append([min(x1,x2), min(y1,y2), min(z1,z2), max(x1,x2), max(y1,y2), max(z1,z2), i])
        
    # Sort by Z
    bricks.sort(key=lambda b: b[2])
    
    # Settle
    # Keep track of max height pattern at (x,y)?
    # Or just O(N^2) check against settled bricks?
    # N ~ 1500. N^2 ~ 2.25M. Feasible.
    
    settled = []
    for b in bricks:
        x1, y1, z1, x2, y2, z2, bid = b
        
        current_z = z1
        target_z = 1 # Floor
        
        # Check intersection with settled bricks below
        # Find max z of settled bricks that intersect xy
        max_below = 0
        for sb in settled:
            if intersect(b, sb):
                max_below = max(max_below, sb[5])
                
        target_z = max_below + 1
        
        drop = current_z - target_z
        b[2] -= drop
        b[5] -= drop
        settled.append(b)
        
        # Keep settled sorted by Z max to optimize?
        settled.sort(key=lambda b: b[5]) # Sort by top Z
        
    # Build support graph
    # supports[A] = [B, C] (A supports B and C)
    # supported_by[B] = [A] (B is supported by A)
    
    supports = defaultdict(set)
    supported_by = defaultdict(set)
    
    # Check all pairs
    # Optimize: check only z proximity
    
    # Re-sort by bottom Z for efficient checking?
    settled.sort(key=lambda b: b[2])
    
    for i, b1 in enumerate(settled):
        # Bricks that might support b1 must be strictly below b1
        # Specifically, top Z == b1 bottom Z - 1
        
        bottom_z = b1[2]
        
        # Check against all settled (optimize later if needed)
        for b2 in settled:
            if b2[6] == b1[6]: continue
            
            # if b2 is directly below b1
            if b2[5] == bottom_z - 1:
                if intersect(b1, b2):
                    supports[b2[6]].add(b1[6])
                    supported_by[b1[6]].add(b2[6])
                    
    # Part 1
    safe_count = 0
    all_bricks = set(b[6] for b in settled)
    
    for b_id in all_bricks:
        # Check if removing b_id causes any fall
        # It causes fall if any brick it supports has NO OTHER support
        can_remove = True
        for supported in supports[b_id]:
            # 'supported' is supported by b_id.
            # check if it has other supports
            if len(supported_by[supported]) == 1:
                # only b_id
                can_remove = False
                break
        if can_remove:
            safe_count += 1
            
    # Part 2
    total_fall = 0
    
    for b_id in all_bricks:
        # Simulate removal
        # BFS
        q = deque([b_id])
        falling = {b_id}
        
        while q:
            current = q.popleft()
            
            # Check bricks supported by current
            # "chain reaction"
            # A brick falls if ALL its supports are falling
            
            for child in supports[current]:
                if child not in falling:
                    # Check supports of child
                    child_supports = supported_by[child]
                    if child_supports.issubset(falling):
                        falling.add(child)
                        q.append(child)
                        
        total_fall += len(falling) - 1 # don't count self
        
    return safe_count, total_fall

def run_tests():
    print("Running tests...")
    example = """1,0,1~1,2,1
0,0,2~2,0,2
0,2,3~2,2,3
0,0,4~0,2,4
2,0,5~2,2,5
0,1,6~2,1,6
1,1,8~1,1,9"""
    
    p1, p2 = solve(example)
    expected_p1 = 5
    expected_p2 = 7
    
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
    data = parse_input("2023-day22.txt")
    p1, p2 = solve(data)
    print("--- Part 1 ---")
    print(f"Result: {p1}")
    print("--- Part 2 ---")
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1_and_2()
