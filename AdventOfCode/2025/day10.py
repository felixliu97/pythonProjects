import re
import math
import sys
from fractions import Fraction
from itertools import product

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        return [parse_line(l.strip()) for l in lines if l.strip()]
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def parse_line(line):
    # Format: [.##.] (3) (1,3) ... {3,5,4,7}
    
    m_lights = re.search(r'\[([.#]+)\]', line)
    if not m_lights:
        return None
    light_str = m_lights.group(1)
    
    buttons_part = line[m_lights.end():]
    m_joltages = re.search(r'\{([\d,]+)\}', buttons_part)
    if not m_joltages:
        return None
        
    joltage_str = m_joltages.group(1)
    joltages = [int(x) for x in joltage_str.split(',')]
    
    buttons_sub = buttons_part[:m_joltages.start()]
    button_matches = re.findall(r'\(([\d,]+)\)', buttons_sub)
    
    buttons = []
    for b in button_matches:
        buttons.append([int(x) for x in b.split(',')])
        
    return {
        'light_str': light_str,
        'buttons': buttons,
        'joltages': joltages
    }

def solve_part1_machine(machine):
    target = [1 if c == '#' else 0 for c in machine['light_str']]
    n = len(target)
    buttons = machine['buttons']
    m = len(buttons)
    
    button_vecs = []
    for b_indices in buttons:
        vec = [0] * n
        for idx in b_indices:
            if idx < n:
                vec[idx] = 1
        button_vecs.append(vec)
        
    min_presses = float('inf')
    
    for i in range(1 << m):
        current = [0] * n
        press_count = 0
        
        for b_idx in range(m):
            if (i >> b_idx) & 1:
                press_count += 1
                vec = button_vecs[b_idx]
                for k in range(n):
                    current[k] ^= vec[k]
        
        if current == target:
            if press_count < min_presses:
                min_presses = press_count
                
    return min_presses if min_presses != float('inf') else 0

def solve_part2_machine(machine):
    target = machine['joltages']
    n = len(target)
    buttons = machine['buttons']
    m = len(buttons)
    
    A = [[0] * m for _ in range(n)]
    for col, b_indices in enumerate(buttons):
        for row in b_indices:
            if row < n:
                A[row][col] = 1
                
    matrix = []
    for r in range(n):
        row = [Fraction(x) for x in A[r]] + [Fraction(target[r])]
        matrix.append(row)
        
    pivot_row = 0
    pivots = {} # col -> row
    free_vars = []
    
    for col in range(m):
        if pivot_row >= n:
            free_vars.append(col)
            continue
            
        sel = -1
        for r in range(pivot_row, n):
            if matrix[r][col] != 0:
                sel = r
                break
        
        if sel == -1:
            free_vars.append(col)
            continue
            
        matrix[pivot_row], matrix[sel] = matrix[sel], matrix[pivot_row]
        
        inv = 1 / matrix[pivot_row][col]
        for c in range(col, m + 1):
            matrix[pivot_row][c] *= inv
            
        for r in range(n):
            if r != pivot_row and matrix[r][col] != 0:
                factor = matrix[r][col]
                for c in range(col, m + 1):
                    matrix[r][c] -= factor * matrix[pivot_row][c]
                    
        pivots[col] = pivot_row
        pivot_row += 1

    for r in range(pivot_row, n):
        if matrix[r][m] != 0:
            return float('inf') 
            
    bounds = []
    for f in free_vars:
        affected_indices = buttons[f]
        if not affected_indices:
            bounds.append(0)
            continue
            
        m_val = float('inf')
        for row_idx in affected_indices:
            if row_idx < n:
                m_val = min(m_val, target[row_idx])
        bounds.append(m_val)
        
    ranges = [range(b + 1) for b in bounds]
    min_total = float('inf')
    
    for free_vals in product(*ranges):
        current_x = {}
        for i, f in enumerate(free_vars):
            current_x[f] = Fraction(free_vals[i])
            
        possible = True
        temp_sum = sum(free_vals)
        
        for p_col, p_row in pivots.items():
            val = matrix[p_row][m]
            for f in free_vars:
                val -= matrix[p_row][f] * current_x[f]
            
            if val.denominator != 1 or val < 0:
                possible = False
                break
            current_x[p_col] = val
            temp_sum += int(val)
            
        if possible:
            if temp_sum < min_total:
                min_total = temp_sum
                
    return min_total if min_total != float('inf') else 0

def run_tests():
    print("Running tests...")
    examples = [
        "[.##.] (3) (1,3) (2) (2,3) (0,2) (0,1) {3,5,4,7}",
        "[...#.] (0,2,3,4) (2,3) (0,4) (0,1,2) (1,2,3,4) {7,5,12,7,2}",
        "[.###.#] (0,1,2,3,4) (0,3,4) (0,1,2,4,5) (1,2) {10,11,11,5,10,5}"
    ]
    
    parsed_examples = [parse_line(l) for l in examples]
    
    # Part 1 Verification
    print("Verifying Part 1 Examples...")
    p1_expected = [2, 3, 2]
    
    for i, m in enumerate(parsed_examples):
        res = solve_part1_machine(m)
        if res == p1_expected[i]:
            print(f"✅ Ex {i+1}: Passed")
        else:
            print(f"❌ Ex {i+1}: Failed (Expected {p1_expected[i]}, Got {res})")
        
    # Part 2 Verification
    print("Verifying Part 2 Examples...")
    p2_expected = [10, 12, 11]
    
    for i, m in enumerate(parsed_examples):
        res = solve_part2_machine(m)
        if res == p2_expected[i]:
            print(f"✅ Ex {i+1}: Passed")
        else:
            print(f"❌ Ex {i+1}: Failed (Expected {p2_expected[i]}, Got {res})")
        
    print("✅ Tests completed!")

def solve_part1():
    print("--- Part 1 ---")
    parsed = parse_input('input-day10.txt')
    total_p1 = 0
    for i, m in enumerate(parsed):
        if not m: continue
        res = solve_part1_machine(m)
        total_p1 += res
    print(f"Result: {total_p1}")

def solve_part2():
    print("--- Part 2 ---")
    parsed = parse_input('input-day10.txt')
    total_p2 = 0
    for i, m in enumerate(parsed):
        if not m: continue
        res = solve_part2_machine(m)
        total_p2 += res
    print(f"Result: {total_p2}")

if __name__ == '__main__':
    run_tests()
    solve_part1()
    solve_part2()
