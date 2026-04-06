import sys
import math

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def solve_race(T, D):
    # h^2 - Th + D < 0
    # Roots: (T +/- sqrt(T^2 - 4D)) / 2
    
    discriminant = T**2 - 4*D
    
    if discriminant < 0:
        return 0
        
    sqrt_d = math.sqrt(discriminant)
    root1 = (T - sqrt_d) / 2
    root2 = (T + sqrt_d) / 2
    
    # We need strict inequality > D
    # So we need range strictly between root1 and root2
    
    start = math.floor(root1 + 1)
    end = math.ceil(root2 - 1)
    
    # Check edge cases where roots are integers (strict inequality means we can't use the root itself)
    # My logic +1 and -1 combined with floor/ceil handles this.
    # Ex: roots 10 and 20. 
    # start = floor(11) = 11. end = ceil(19) = 19. Count = 19 - 11 + 1 = 9.
    # (11, 12, ... 19). 10 and 20 give exact match (Distance D), but we need > D.
    
    # What if root1 is 10.0?
    # start = floor(11.0) = 11. Correct.
    # What if root1 is 10.1?
    # start = floor(11.1) = 11. Correct. (11 > 10.1)
    
    if start > end:
        return 0
        
    return end - start + 1

def solve(data):
    lines = data.split('\n')
    times = list(map(int, lines[0].split(':')[1].split()))
    dists = list(map(int, lines[1].split(':')[1].split()))
    
    # Part 1
    p1 = 1
    for t_val, d_val in zip(times, dists):
        ways = solve_race(t_val, d_val)
        p1 *= ways
        
    # Part 2
    # Ignore spaces
    big_t = int(lines[0].split(':')[1].replace(' ', ''))
    big_d = int(lines[1].split(':')[1].replace(' ', ''))
    
    p2 = solve_race(big_t, big_d)
    
    return p1, p2

def run_tests():
    print("Running tests...")
    example = """Time:      7  15   30
Distance:  9  40  200"""
    
    p1, p2 = solve(example)
    expected_p1 = 288
    expected_p2 = 71503
    
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
    data = parse_input("2023-day6.txt")
    p1, p2 = solve(data)
    print("--- Part 1 ---")
    print(f"Result: {p1}")
    print("--- Part 2 ---")
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1_and_2()
