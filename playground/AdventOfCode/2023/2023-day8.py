import sys
import math
import itertools
# Python 3.9+ has math.lcm, but if older python, need to implement.
# I'll implement gcd based lcm just in case.

def lcm(a, b):
    return abs(a*b) // math.gcd(a, b)

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def solve(data):
    lines = data.split('\n')
    instructions = lines[0].strip()
    
    nodes = {}
    for line in lines[2:]:
        # AAA = (BBB, CCC)
        parts = line.split('=')
        key = parts[0].strip()
        val_part = parts[1].strip()[1:-1]
        left, right = val_part.split(',')
        nodes[key] = (left.strip(), right.strip())
        
    # Part 1
    # Check if AAA exists (sometimes example for P2 doesn't have AAA)
    p1 = 0
    if 'AAA' in nodes:
        current = 'AAA'
        steps = 0
        cycle = itertools.cycle(instructions)
        for move in cycle:
            if current == 'ZZZ':
                break
            steps += 1
            if move == 'L':
                current = nodes[current][0]
            else:
                current = nodes[current][1]
        p1 = steps
        
    # Part 2
    starts = [n for n in nodes if n.endswith('A')]
    cycle_lengths = []
    
    for start in starts:
        current = start
        steps = 0
        cycle_iter = itertools.cycle(instructions)
        for move in cycle_iter:
            if current.endswith('Z'):
                cycle_lengths.append(steps)
                break
            steps += 1
            if move == 'L':
                current = nodes[current][0]
            else:
                current = nodes[current][1]
                
    p2 = cycle_lengths[0]
    for length in cycle_lengths[1:]:
        p2 = lcm(p2, length)
        
    return p1, p2

def run_tests():
    print("Running tests...")
    example = """RL

AAA = (BBB, CCC)
BBB = (DDD, EEE)
CCC = (ZZZ, GGG)
DDD = (DDD, DDD)
EEE = (EEE, EEE)
GGG = (GGG, GGG)
ZZZ = (ZZZ, ZZZ)"""
    
    p1, _ = solve(example) # Part 2 logic might fail on this specific example if nodes don't align for ghosts, but logic is sound.
    expected_p1 = 2
    
    if p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1}")
        
    example2 = """LR

11A = (11B, XXX)
11B = (XXX, 11Z)
11Z = (11B, XXX)
22A = (22B, XXX)
22B = (22C, 22C)
22C = (22Z, 22Z)
22Z = (22B, 22B)
XXX = (XXX, XXX)"""
    
    _, p2 = solve(example2)
    expected_p2 = 6
    if p2 == expected_p2:
         print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {p2}")

    print("✅ Tests completed!")

def solve_part1_and_2():
    data = parse_input("2023-day8.txt")
    p1, p2 = solve(data)
    print("--- Part 1 ---")
    print(f"Result: {p1}")
    print("--- Part 2 ---")
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1_and_2()
