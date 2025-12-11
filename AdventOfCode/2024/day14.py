import sys
import re
import math

def parse_input(filename):
    robots = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                if line.strip():
                    # p=0,4 v=3,-3
                    # Extract numbers
                    parts = list(map(int, re.findall(r'-?\d+', line)))
                    if len(parts) == 4:
                        robots.append(((parts[0], parts[1]), (parts[2], parts[3])))
        return robots
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def simulate_robot(px, py, vx, vy, time, width, height):
    npx = (px + vx * time) % width
    npy = (py + vy * time) % height
    return npx, npy

def count_quadrants(robots, width, height):
    mx = width // 2
    my = height // 2
    
    q1 = 0
    q2 = 0
    q3 = 0
    q4 = 0
    
    for (px, py), _ in robots:
        if px == mx or py == my:
            continue
            
        if px < mx and py < my:
            q1 += 1
        elif px > mx and py < my:
            q2 += 1
        elif px < mx and py > my:
            q3 += 1
        elif px > mx and py > my:
            q4 += 1
            
    return q1, q2, q3, q4

def print_grid(robots, width, height):
    grid = [['.' for _ in range(width)] for _ in range(height)]
    for (px, py), _ in robots:
        grid[py][px] = '#' # Simplification: multiple robots marked as #
        
    for row in grid:
        print("".join(row))

def calculate_variance(positions):
    if not positions:
        return 0
    mean_x = sum(p[0] for p in positions) / len(positions)
    mean_y = sum(p[1] for p in positions) / len(positions)
    
    var_x = sum((p[0] - mean_x) ** 2 for p in positions) / len(positions)
    var_y = sum((p[1] - mean_y) ** 2 for p in positions) / len(positions)
    
    return var_x + var_y

def run_tests():
    print("Running tests...")
    
    example_input = """p=0,4 v=3,-3
p=6,3 v=-1,-3
p=10,3 v=-1,2
p=2,0 v=2,-1
p=0,0 v=1,3
p=3,0 v=-2,-2
p=7,6 v=-1,-3
p=3,0 v=-1,-2
p=9,3 v=2,3
p=7,3 v=-1,2
p=2,4 v=2,-3
p=9,5 v=-3,-3"""
    
    robots = []
    for line in example_input.strip().split('\n'):
        parts = list(map(int, re.findall(r'-?\d+', line)))
        if len(parts) == 4:
            robots.append(((parts[0], parts[1]), (parts[2], parts[3])))
            
    width = 11
    height = 7
    time = 100
    
    final_positions = []
    for (px, py), (vx, vy) in robots:
        npx, npy = simulate_robot(px, py, vx, vy, time, width, height)
        final_positions.append(((npx, npy), (vx, vy)))
        
    q1, q2, q3, q4 = count_quadrants(final_positions, width, height)
    safety_factor = q1 * q2 * q3 * q4
    
    print(f"Test Part 1 Result: {safety_factor} (Expected 12)")
    expected_p1 = 12
    if safety_factor == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {safety_factor}")
        
    # Part 2 is visual/pattern based, might skip automated test for tree detection on small grid
    print("✅ Tests completed!")

def solve_part1():
    print("--- Part 1 ---")
    robots = parse_input("input-day14.txt")
    
    width = 101
    height = 103
    time = 100
    
    final_positions = []
    for (px, py), (vx, vy) in robots:
        npx, npy = simulate_robot(px, py, vx, vy, time, width, height)
        final_positions.append(((npx, npy), (vx, vy)))
        
    q1, q2, q3, q4 = count_quadrants(final_positions, width, height)
    safety_factor = q1 * q2 * q3 * q4
    print(f"Result: {safety_factor}")

def solve_part2():
    print("--- Part 2 ---")
    robots = parse_input("input-day14.txt")
    
    width = 101
    height = 103
    
    # Heuristic: Minimum Variance / Clustering
    # The tree usually appears when robots cluster together significantly.
    # Searching for minimum variance is a good proxy.
    
    min_variance = float('inf')
    best_time = -1
    
    # Search reasonable range. The cycles should repeat at LCM(101, 103) = 10403
    for t in range(width * height + 1):
        positions = []
        for (px, py), (vx, vy) in robots:
            npx, npy = simulate_robot(px, py, vx, vy, t, width, height)
            positions.append((npx, npy))
            
        var = calculate_variance(positions)
        if var < min_variance:
            min_variance = var
            best_time = t
            # Optional: Print grid to verify
            # print(f"Time {t} Variance {var}")
            # print_grid([(p, (0,0)) for p in positions], width, height)
            
    print(f"Result: {best_time}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
