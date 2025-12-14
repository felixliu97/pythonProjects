import re
import math
import sys
from fractions import Fraction
from itertools import product
import itertools

# Set recursion limit higher just in case
sys.setrecursionlimit(2000)

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
    # Solve Ax = b over GF(2)
    target = [1 if c == '#' else 0 for c in machine['light_str']]
    n_rows = len(target)
    buttons = machine['buttons']
    n_cols = len(buttons)
    
    # Construct matrix [A | b]
    matrix = []
    for r in range(n_rows):
        row = []
        for c in range(n_cols):
            if r in buttons[c]:
                row.append(1)
            else:
                row.append(0)
        row.append(target[r])
        matrix.append(row)
        
    # Gaussian Elimination
    pivot_row = 0
    pivots = {} # col -> row
    free_vars = []
    
    for col in range(n_cols):
        if pivot_row >= n_rows:
            free_vars.append(col)
            continue
            
        # Find pivot
        sel = -1
        for r in range(pivot_row, n_rows):
            if matrix[r][col] == 1:
                sel = r
                break
        
        if sel == -1:
            free_vars.append(col)
            continue
            
        # Swap
        matrix[pivot_row], matrix[sel] = matrix[sel], matrix[pivot_row]
        
        # Eliminate
        for r in range(n_rows):
            if r != pivot_row and matrix[r][col] == 1:
                for c in range(col, n_cols + 1):
                    matrix[r][c] ^= matrix[pivot_row][c]
                    
        pivots[col] = pivot_row
        pivot_row += 1
        
    # Check consistency
    for r in range(pivot_row, n_rows):
        if matrix[r][n_cols] == 1:
            return 0 

    # Try all assignments of free variables to minimize Hamming weight
    min_presses = float('inf')
    
    for free_vals in itertools.product([0, 1], repeat=len(free_vars)):
        x_vals = {}
        current_presses = 0
        
        for i, f_col in enumerate(free_vars):
            val = free_vals[i]
            x_vals[f_col] = val
            if val == 1:
                current_presses += 1
                
        # Determine pivot variables
        possible_assignment = True
        
        # We iterate in reverse order of pivots to back-substitute (though RREF makes it direct)
        for col in sorted(pivots.keys(), reverse=True):
            row = pivots[col]
            rhs = matrix[row][n_cols]
            
            sum_free = 0
            for f in free_vars:
                # In RREF, pivot row only has 1 at 'col', and potentially non-zeros at free cols
                if matrix[row][f] == 1:
                    sum_free ^= x_vals[f]
            
            val = rhs ^ sum_free
            x_vals[col] = val
            if val == 1:
                current_presses += 1
        
        if current_presses < min_presses:
            min_presses = current_presses
            
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
    
    pivots_list = [] # List of (col, row)
    for col in sorted(pivots.keys()):
        pivots_list.append((col, pivots[col]))
        
    min_total = [float('inf')]
    
    pivot_deps = []
    for p_col, p_row in pivots_list:
        deps = []
        for i, f in enumerate(free_vars):
            coeff = matrix[p_row][f]
            if coeff != 0:
                deps.append((i, coeff))
        rhs = matrix[p_row][m]
        pivot_deps.append({'col': p_col, 'rhs': rhs, 'deps': deps})

    def backtrack(idx, current_free_vals, current_sum):
        if current_sum >= min_total[0]:
            return

        if idx == len(free_vars):
            total_sum = current_sum
            possible = True
            
            for p_info in pivot_deps:
                val = p_info['rhs']
                for f_idx, coeff in p_info['deps']:
                    val -= coeff * current_free_vals[f_idx]
                
                if val.denominator != 1 or val < 0:
                    possible = False
                    break
                total_sum += int(val)
                if total_sum >= min_total[0]:
                    possible = False
                    break
            
            if possible:
                if total_sum < min_total[0]:
                    min_total[0] = total_sum
            return

        r_range = ranges[idx]
        for val in r_range:
             current_free_vals.append(Fraction(val))
             backtrack(idx + 1, current_free_vals, current_sum + val)
             current_free_vals.pop()

    backtrack(0, [], 0)
    
    return min_total[0] if min_total[0] != float('inf') else 0

def run_tests():
    print("Running tests...")
    examples = [
        "[.##.] (3) (1,3) (2) (2,3) (0,2) (0,1) {3,5,4,7}",
        "[...#.] (0,2,3,4) (2,3) (0,4) (0,1,2) (1,2,3,4) {7,5,12,7,2}",
        "[.###.#] (0,1,2,3,4) (0,3,4) (0,1,2,4,5) (1,2) {10,11,11,5,10,5}"
    ]
    
    parsed_examples = [parse_line(l) for l in examples]
    
    print("Verifying Part 1 Examples...")
    p1_expected = [2, 3, 2]
    
    for i, m in enumerate(parsed_examples):
        res = solve_part1_machine(m)
        if res == p1_expected[i]:
            print(f"✅ Ex {i+1}: Passed")
        else:
            print(f"❌ Ex {i+1}: Failed (Expected {p1_expected[i]}, Got {res})")
        
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
    parsed = parse_input('2025-day10.txt')
    total_p1 = 0
    for i, m in enumerate(parsed):
        if not m: continue
        res = solve_part1_machine(m)
        total_p1 += res
    print(f"Result: {total_p1}")

def solve_part2():
    print("--- Part 2 ---")
    parsed = parse_input('2025-day10.txt')
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
