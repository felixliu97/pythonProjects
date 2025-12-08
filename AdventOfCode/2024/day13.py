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
        print(f"Error: File {filename} not found.")
        return []
    except Exception as e:
        print(f"Error parsing input: {e}")
        return []
        
    return machines

def solve_machine(m, offset=0, limit=None):
    # Cramer's Rule
    # a * Ax + b * Bx = Px
    # a * Ay + b * By = Py
    
    Px = m['Px'] + offset
    Py = m['Py'] + offset
    
    det = m['Ax'] * m['By'] - m['Ay'] * m['Bx']
    
    if det == 0:
        return 0 # No unique solution (parallel vectors)
        
    # Numerators
    num_a = Px * m['By'] - Py * m['Bx']
    num_b = m['Ax'] * Py - m['Ay'] * Px
    
    # Check if integer solution exists
    if num_a % det == 0 and num_b % det == 0:
        a = num_a // det
        b = num_b // det
        
        # Check constraints
        if a >= 0 and b >= 0:
            if limit is not None:
                if a <= limit and b <= limit:
                    return 3 * a + b
            else:
                return 3 * a + b
            
    return 0

def solve(filename):
    machines = parse_input(filename)
    total_tokens_p1 = 0
    total_tokens_p2 = 0
    
    for m in machines:
        total_tokens_p1 += solve_machine(m, offset=0, limit=100)
        total_tokens_p2 += solve_machine(m, offset=10000000000000, limit=None)
            
    return total_tokens_p1, total_tokens_p2

def test():
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
    assert total == 480, f"Expected 480, got {total}"
    
    # Test Part 2 (Manual check on specific known winnable cases from prompt if detailed)
    # The prompt says: "Now, it is only possible to win a prize on the second and fourth claw machines."
    # Let's verify we get a positive cost for 2nd and 4th, and 0 for others.
    
    costs = []
    for m in machines:
        costs.append(solve_machine(m, offset=10000000000000, limit=None))
        
    print(f"Test Part 2 Costs: {costs}")
    assert costs[0] == 0  # 1st
    assert costs[1] > 0   # 2nd
    assert costs[2] == 0  # 3rd
    assert costs[3] > 0   # 4th

if __name__ == "__main__":
    test()
    print("Tests passed!")
    p1, p2 = solve("input-day13.txt")
    print(f"Part 1 Result: {p1}")
    print(f"Part 2 Result: {p2}")
