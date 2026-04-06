import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def solve_polygon_area(lines):
    # Shoelace formula to get Area
    # Pick's Theorem: A = i + b/2 - 1
    # We want Total Area (Interior + Boundary) = i + b
    # i = A - b/2 + 1
    # Total = A - b/2 + 1 + b = A + b/2 + 1.
    
    # Vertices
    # Note: The "lines" are boundaries of 1x1 cells.
    # The vertices are effectively the corners?
    # Or center points?
    # If we trace center points, Shoelace gives area of polygon through centers.
    # The boundary length 'b' corresponds to the perimeter.
    # The formula (A + b/2 + 1) works for this grid polygon interpretation.
    
    r, c = 0, 0
    points = [(0, 0)]
    perimeter = 0
    
    # Directions: R, D, L, U
    # Be careful with orientation. 
    # U/D/L/R
    
    for direction, dist in lines:
        dr, dc = 0, 0
        if direction == 'R': dc = 1
        elif direction == 'L': dc = -1
        elif direction == 'U': dr = -1
        elif direction == 'D': dr = 1
        
        r += dr * dist
        c += dc * dist
        points.append((r, c))
        perimeter += dist
        
    # Shoelace Area
    # sum(x_i * y_{i+1} - x_{i+1} * y_i) / 2
    # Here x=c, y=r?
    
    area_doubled = 0
    for i in range(len(points) - 1):
        r1, c1 = points[i]
        r2, c2 = points[i+1]
        area_doubled += (r1 * c2 - r2 * c1) # or c1*r2 - c2*r1
        
    area = abs(area_doubled) // 2
    
    total_points = area + perimeter // 2 + 1
    return total_points

def solve(data):
    lines = data.split('\n')
    
    instructions_p1 = []
    instructions_p2 = []
    
    for line in lines:
        parts = line.split()
        d_char = parts[0]
        dist = int(parts[1])
        hex_code = parts[2][2:-1] # (#70c710) -> 70c710
        
        instructions_p1.append((d_char, dist))
        
        # P2 decode
        # 0: R, 1: D, 2: L, 3: U
        dist_p2 = int(hex_code[:5], 16)
        dir_digit = int(hex_code[5])
        
        dir_map_p2 = ['R', 'D', 'L', 'U']
        dir_p2 = dir_map_p2[dir_digit]
        
        instructions_p2.append((dir_p2, dist_p2))
        
    p1 = solve_polygon_area(instructions_p1)
    p2 = solve_polygon_area(instructions_p2)
    
    return p1, p2

def run_tests():
    print("Running tests...")
    example = """R 6 (#70c710)
D 5 (#0dc571)
L 2 (#5713f0)
D 2 (#d2c081)
R 2 (#59c680)
D 2 (#411b91)
L 5 (#8ceee2)
U 2 (#caa173)
L 1 (#1b58a2)
U 2 (#caa171)
R 2 (#7807d2)
U 3 (#a77fa3)
L 2 (#015232)
U 2 (#7a21e3)"""
    
    p1, p2 = solve(example)
    expected_p1 = 62
    expected_p2 = 952408144115
    
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
    data = parse_input("2023-day18.txt")
    p1, p2 = solve(data)
    print("--- Part 1 ---")
    print(f"Result: {p1}")
    print("--- Part 2 ---")
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1_and_2()
