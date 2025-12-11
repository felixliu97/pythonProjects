import sys

def parse_input(filename):
    points = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                if line.strip():
                    x, y = map(int, line.strip().split(','))
                    points.append((x, y))
        return points
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def calculate_max_area(points):
    max_area = 0
    # Brute force O(N^2)
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            x1, y1 = points[i]
            x2, y2 = points[j]
            
            width = abs(x1 - x2) + 1
            height = abs(y1 - y2) + 1
            area = width * height
            
            if area > max_area:
                max_area = area
                
    return max_area

# --- Part 2 Logic ---

def is_point_inside_polygon(x, y, poly):
    # Ray casting algorithm
    n = len(poly)
    inside = False
    p1x, p1y = poly[0]
    for i in range(n + 1):
        p2x, p2y = poly[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def edge_intersects_rect(r_x1, r_y1, r_x2, r_y2, p1_x, p1_y, p2_x, p2_y):
    # Check if a polygon edge segment (p1-p2) goes THROUGH the rectangle (strictly not just touching borders)
    # Rectangle range [r_x1, r_x2] x [r_y1, r_y2] inclusive
    
    min_px, max_px = min(p1_x, p2_x), max(p1_x, p2_x)
    min_py, max_py = min(p1_y, p2_y), max(p1_y, p2_y)

    # If edge is horizontal: y is constant
    if p1_y == p2_y:
        y = p1_y
        # Edge passes through horizontally if y is STRICTLY inside y range
        # AND x range overlaps
        if r_y1 < y < r_y2:
            # Overlap check (strict)
             if max(r_x1, min_px) < min(r_x2, max_px):
                return True

    # If edge is vertical: x is constant
    elif p1_x == p2_x:
        x = p1_x
        # Edge passes through vertically if x is STRICTLY inside x range
        if r_x1 < x < r_x2:
            if max(r_y1, min_py) < min(r_y2, max_py):
                return True

    return False

def calculate_max_area_part2(points):
    # 1. Generate all rectangles
    rects = []
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            x1, y1 = points[i]
            x2, y2 = points[j]
            width = abs(x1 - x2) + 1
            height = abs(y1 - y2) + 1
            area = width * height
            rects.append({
                'area': area,
                'min_x': min(x1, x2), 'max_x': max(x1, x2),
                'min_y': min(y1, y2), 'max_y': max(y1, y2)
            })

    # 2. Sort by Area Descending
    rects.sort(key=lambda x: x['area'], reverse=True)

    # 3. Validation
    # Pre-calculate poly edges
    poly = points # The points are already in order

    # print(f"Checking {len(rects)} candidate rectangles...")
    
    for r in rects:
        # A. Center point check
        cx = (r['min_x'] + r['max_x']) / 2.0
        cy = (r['min_y'] + r['max_y']) / 2.0
        
        if not is_point_inside_polygon(cx, cy, poly):
            continue
            
        # B. Edge intersection check
        invalid_edge = False
        n = len(poly)
        p1 = poly[0]
        for i in range(1, n + 1):
            p2 = poly[i % n]
            
            if edge_intersects_rect(r['min_x'], r['min_y'], r['max_x'], r['max_y'], 
                                    p1[0], p1[1], p2[0], p2[1]):
                invalid_edge = True
                break
            p1 = p2
        
        if not invalid_edge:
            return r['area']
            
    return 0

def run_tests():
    print("Running tests...")
    example_data = [
        (7,1), (11,1), (11,7), (9,7),
        (9,5), (2,5), (2,3), (7,3)
    ]
    
    print("Verifying Part 1 Example...")
    area = calculate_max_area(example_data)
    expected_p1 = 50
    if area == expected_p1:
        print(f"✅ Part 1 Passed")
    else:
        print(f"❌ Part 1 Failed: Expected {expected_p1}, Got {area}")

    print("Verifying Part 2 Example...")
    area_p2 = calculate_max_area_part2(example_data)
    expected_p2 = 24
    if area_p2 == expected_p2:
        print(f"✅ Part 2 Passed")
    else:
        print(f"❌ Part 2 Failed: Expected {expected_p2}, Got {area_p2}")
        
    print("✅ Tests completed!")

def solve_part1():
    print("--- Part 1 ---")
    points = parse_input('input-day9.txt')
    result_p1 = calculate_max_area(points)
    print(f"Result: {result_p1}")

def solve_part2():
    print("--- Part 2 ---")
    points = parse_input('input-day9.txt')
    result_p2 = calculate_max_area_part2(points)
    print(f"Result: {result_p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
