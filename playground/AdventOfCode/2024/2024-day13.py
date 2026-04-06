import sys
import re

def parse_input(filename):
    machines = []
    try:
        with open(filename, 'r') as f:
            content = f.read().strip()
            
        blocks = content.split('\n\n')
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                # Button A: X+94, Y+34
                ax, ay = map(int, re.findall(r'X\+(\d+), Y\+(\d+)', lines[0])[0])
                # Button B: X+22, Y+67
                bx, by = map(int, re.findall(r'X\+(\d+), Y\+(\d+)', lines[1])[0])
                # Prize: X=8400, Y=5400
                px, py = map(int, re.findall(r'X=(\d+), Y=(\d+)', lines[2])[0])
                machines.append({'Ax': ax, 'Ay': ay, 'Bx': bx, 'By': by, 'Px': px, 'Py': py})
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing input: {e}")
        sys.exit(1)
        
    return machines

def run_tests():
    print("Running tests...")
    
    example_input = """Button A: X+94, Y+34
Button B: X+22, Y+67
Prize: X=8400, Y=5400

Button A: X+26, Y+66
Button B: X+67, Y+21
Prize: X=12748, Y=12176

Button A: X+17, Y+86
Button B: X+84, Y+37
Prize: X=7870, Y=6450

Button A: X+69, Y+23
Button B: X+27, Y+71
Prize: X=18641, Y=10279"""

    machines = []
    blocks = example_input.split('\n\n')
    for block in blocks:
        lines = block.strip().split('\n')
        ax, ay = map(int, re.findall(r'X\+(\d+), Y\+(\d+)', lines[0])[0])
        bx, by = map(int, re.findall(r'X\+(\d+), Y\+(\d+)', lines[1])[0])
        px, py = map(int, re.findall(r'X=(\d+), Y=(\d+)', lines[2])[0])
        machines.append({'Ax': ax, 'Ay': ay, 'Bx': bx, 'By': by, 'Px': px, 'Py': py})
    
    # Test Part 1
    total = 0
    for m in machines:
        total += solve_machine(m, offset=0, limit=100)
    print(f"Test Part 1 Result: {total}")
    expected_p1 = 480
    if total == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {total}")
    
    # Test Part 2 (Manual verification logic from original file)
    costs = []
    for m in machines:
        costs.append(solve_machine(m, offset=10000000000000, limit=None))
        
    print(f"Test Part 2 Costs: {costs}")
    if costs[0] == 0 and costs[1] > 0 and costs[2] == 0 and costs[3] > 0:
        print("✅ Part 2 Checks passed!")
    else:
        print("❌ Part 2 Checks failed")
        
    print("✅ Tests completed!")

def solve_machine(m, offset=0, limit=None):
    # Cramer's Rule
    # a * Ax + b * Bx = Px
    # a * Ay + b * By = Py
    
    Px = m['Px'] + offset
    Py = m['Py'] + offset
    
    det = m['Ax'] * m['By'] - m['Ay'] * m['Bx']
    
    if det == 0:
        return 0 
        
    num_a = Px * m['By'] - Py * m['Bx']
    num_b = m['Ax'] * Py - m['Ay'] * Px
    
    if num_a % det == 0 and num_b % det == 0:
        a = num_a // det
        b = num_b // det
        
        if a >= 0 and b >= 0:
            if limit is not None:
                if a <= limit and b <= limit:
                    return 3 * a + b
            else:
                return 3 * a + b
            
    return 0

def solve_part1():
    print("--- Part 1 ---")
    machines = parse_input("2024-day13.txt")
    total = 0
    for m in machines:
        total += solve_machine(m, offset=0, limit=100)
    print(f"Result: {total}")

def solve_part2():
    print("--- Part 2 ---")
    machines = parse_input("2024-day13.txt")
    total = 0
    for m in machines:
        total += solve_machine(m, offset=10000000000000, limit=None)
    print(f"Result: {total}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
