import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def parse_hailstones(data):
    hailstones = []
    for line in data.split('\n'):
        pos_str, vel_str = line.split('@')
        px, py, pz = map(int, pos_str.split(','))
        vx, vy, vz = map(int, vel_str.split(','))
        hailstones.append(((px, py, pz), (vx, vy, vz)))
    return hailstones

def intersection_2d(h1, h2, min_coord, max_coord):
    # p1 + v1 * t1 = p2 + v2 * t2
    # x1 + vx1 * t1 = x2 + vx2 * t2
    # y1 + vy1 * t1 = y2 + vy2 * t2
    
    (px1, py1, _), (vx1, vy1, _) = h1
    (px2, py2, _), (vx2, vy2, _) = h2
    
    # Solve for t1, t2
    # vx1 * t1 - vx2 * t2 = x2 - x1
    # vy1 * t1 - vy2 * t2 = y2 - y1
    
    det = vx1 * (-vy2) - vy1 * (-vx2)
    # det = -vx1*vy2 + vy1*vx2 = vy1*vx2 - vx1*vy2
    
    if det == 0:
        return False # Parallel
        
    dx = px2 - px1
    dy = py2 - py1
    
    # Cramer's Rule
    # det_t1 = dx * (-vy2) - dy * (-vx2) = -dx*vy2 + dy*vx2
    # det_t2 = vx1 * dy - vy1 * dx
    
    det_t1 = dx * (-vy2) - dy * (-vx2)
    det_t2 = vx1 * dy - vy1 * dx
    
    t1 = det_t1 / det
    t2 = det_t2 / det
    
    if t1 < 0 or t2 < 0:
        return False # Past
        
    ix = px1 + vx1 * t1
    iy = py1 + vy1 * t1
    
    if min_coord <= ix <= max_coord and min_coord <= iy <= max_coord:
        return True
    return False

from fractions import Fraction

def solve_part2_linear(hailstones):
    h1 = hailstones[0]
    h2 = hailstones[1]
    h3 = hailstones[2]
    
    p1, v1 = h1
    p2, v2 = h2
    p3, v3 = h3
    
    def sub(a, b):
        return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
    
    def cross(a, b):
        return (
            a[1]*b[2] - a[2]*b[1],
            a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0]
        )
        
    def cross_matrix(v):
        vx, vy, vz = v
        return [
            [0, -vz, vy],
            [vz, 0, -vx],
            [-vy, vx, 0]
        ]
        
    matrix = []
    rhs = []
    
    # Pair 1: H1, H2
    # Pr x (V1 - V2) + (P1 - P2) x Vr = P1 x V1 - P2 x V2
    # Matrix term 1 for P: (V2 - V1) x P  => cross_matrix(V2-V1)
    # Matrix term 2 for V: (P1 - P2) x V  => cross_matrix(P1-P2)
    
    dv12 = sub(v2, v1)
    dp12 = sub(p1, p2)
    rhs12 = sub(cross(p1, v1), cross(p2, v2))
    
    m1_L = cross_matrix(dv12) 
    m1_R = cross_matrix(dp12) 
    
    for i in range(3):
        row = [Fraction(x) for x in m1_L[i]] + [Fraction(x) for x in m1_R[i]]
        matrix.append(row)
        rhs.append(Fraction(rhs12[i]))
        
    # Pair 2: H1, H3
    dv13 = sub(v3, v1)
    dp13 = sub(p1, p3)
    rhs13 = sub(cross(p1, v1), cross(p3, v3))
    
    m2_L = cross_matrix(dv13)
    m2_R = cross_matrix(dp13)
    
    for i in range(3):
        row = [Fraction(x) for x in m2_L[i]] + [Fraction(x) for x in m2_R[i]]
        matrix.append(row)
        rhs.append(Fraction(rhs13[i]))
        
    # Solve Gaussian
    N = 6
    aug = [matrix[i] + [rhs[i]] for i in range(N)]
    
    for i in range(N):
        pivot = i
        for j in range(i+1, N):
            if abs(aug[j][i]) > abs(aug[pivot][i]):
                pivot = j
        aug[i], aug[pivot] = aug[pivot], aug[i]
        
        div = aug[i][i]
        # if div == 0: continue
        for j in range(i, N+1):
            aug[i][j] /= div
            
        for k in range(N):
            if k != i:
                factor = aug[k][i]
                for j in range(i, N+1):
                    aug[k][j] -= factor * aug[i][j]
                    
    solution = [aug[i][N] for i in range(N)]
    
    prx, pry, prz = solution[0], solution[1], solution[2]
    
    return int(prx + pry + prz)

def solve(data, test_mode=False):
    hailstones = parse_hailstones(data)
    
    # Part 1
    min_c = 200000000000000
    max_c = 400000000000000
    if test_mode:
        min_c = 7
        max_c = 27
        
    count = 0
    for i in range(len(hailstones)):
        for j in range(i+1, len(hailstones)):
            if intersection_2d(hailstones[i], hailstones[j], min_c, max_c):
                count += 1
                
    p1 = count
    
    # Part 2
    p2 = solve_part2_linear(hailstones)
    
    return p1, p2

def run_tests():
    print("Running tests...")
    example = """19, 13, 30 @ -2,  1, -2
18, 19, 22 @ -1, -1, -2
20, 25, 34 @ -2, -2, -4
12, 31, 28 @ -1, -2, -1
20, 19, 15 @  1, -5, -3"""
    
    p1, p2 = solve(example, test_mode=True)
    expected_p1 = 2
    expected_p2 = 47
    
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
    data = parse_input("2023-day24.txt")
    p1, p2 = solve(data)
    print("--- Part 1 ---")
    print(f"Result: {p1}")
    print("--- Part 2 ---")
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1_and_2()
