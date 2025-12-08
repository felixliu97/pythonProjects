import re

def parse_input(filename):
    robots = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                # p=0,4 v=3,-3
                match = re.search(r'p=(-?\d+),(-?\d+) v=(-?\d+),(-?\d+)', line)
                if match:
                    px, py, vx, vy = map(int, match.groups())
                    robots.append({'p': (px, py), 'v': (vx, vy)})
    except FileNotFoundError:
        print(f"Error: File {filename} not found.")
        return []
    return robots

def simulate(robots, width, height, seconds):
    final_positions = []
    for r in robots:
        px, py = r['p']
        vx, vy = r['v']
        
        # Calculate new position with wrapping
        nx = (px + vx * seconds) % width
        ny = (py + vy * seconds) % height
        
        final_positions.append((nx, ny))
    return final_positions

def get_safety_factor(positions, width, height):
    mx = width // 2
    my = height // 2
    
    q1 = 0 # Top-Left
    q2 = 0 # Top-Right
    q3 = 0 # Bottom-Left
    q4 = 0 # Bottom-Right
    
    for x, y in positions:
        if x == mx or y == my:
            continue
            
        if x < mx and y < my:
            q1 += 1
        elif x > mx and y < my:
            q2 += 1
        elif x < mx and y > my:
            q3 += 1
        elif x > mx and y > my:
            q4 += 1
            
    return q1 * q2 * q3 * q4

def print_grid(positions, width, height):
    grid = [['.' for _ in range(width)] for _ in range(height)]
    for x, y in positions:
        grid[y][x] = '#'
    
    for row in grid:
        print("".join(row))

def calculate_clustering_score(positions):
    # Score is the number of robots that have at least one neighbor
    # This is a good heuristic for "forming a picture"
    pos_set = set(positions)
    score = 0
    for x, y in positions:
        has_neighbor = False
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                if (x + dx, y + dy) in pos_set:
                    has_neighbor = True
                    break
            if has_neighbor:
                break
        if has_neighbor:
            score += 1
    return score

def solve(filename):
    robots = parse_input(filename)
    if not robots:
        return 0, 0
        
    width = 101
    height = 103
    
    # Part 1
    final_positions_p1 = simulate(robots, width, height, 100)
    part1_result = get_safety_factor(final_positions_p1, width, height)
    
    # Part 2
    # Search for the Christmas tree
    # The pattern repeats every width * height seconds (since 101 and 103 are prime)
    max_score = -1
    best_t = -1
    best_positions = []
    
    # Heuristic search
    for t in range(width * height):
        # We can optimize simulation by updating iteratively, but simple simulate is fast enough
        # Actually, let's optimize slightly by pre-calculating starts
        # But for 10000 steps with 500 robots, naive is fine (~5e6 ops)
        current_positions = simulate(robots, width, height, t)
        score = calculate_clustering_score(current_positions)
        
        if score > max_score:
            max_score = score
            best_t = t
            best_positions = current_positions
            
    # Visualize the best one to confirm
    print(f"\n--- Potential Tree Found at t={best_t} (Score: {max_score}) ---")
    print_grid(best_positions, width, height)
    print("---------------------------------------------------\n")
    
    return part1_result, best_t

if __name__ == "__main__":
    p1, p2 = solve("input-day14.txt")
    print(f"Part 1 Result: {p1}")
    print(f"Part 2 Result: {p2}")
