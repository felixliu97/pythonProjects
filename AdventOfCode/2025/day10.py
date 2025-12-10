import re
import math
from fractions import Fraction
from itertools import product

def parse_line(line):
    # Format: [.##.] (3) (1,3) ... {3,5,4,7}
    
    # Extract lights
    m_lights = re.search(r'\[([.#]+)\]', line)
    if not m_lights:
        return None
    light_str = m_lights.group(1)
    
    # Extract buttons
    # Buttons are in parens (1,2,3)
    # We find all ( ... ) parts
    # But wait, lights are in [], joltages in {}
    # So we can just find all (...) matches
    
    buttons_part = line[m_lights.end():]
    m_joltages = re.search(r'\{([\d,]+)\}', buttons_part)
    if not m_joltages:
        # Maybe handle case where joltages are missing if that's possible (unlikely based on problem)
        return None
        
    joltage_str = m_joltages.group(1)
    joltages = [int(x) for x in joltage_str.split(',')]
    
    # Buttons are between lights and joltages
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
    # Target: light_str to array of 0/1
    # Buttons: indices to arrays
    # Solve sum(buttons) = target mod 2
    # Minimize count
    
    target = [1 if c == '#' else 0 for c in machine['light_str']]
    n = len(target)
    buttons = machine['buttons']
    m = len(buttons)
    
    # Build button vectors
    button_vecs = []
    for b_indices in buttons:
        vec = [0] * n
        for idx in b_indices:
            if idx < n:
                vec[idx] = 1
        button_vecs.append(vec)
        
    min_presses = float('inf')
    
    # Brute force 2^M. Max M is small (~15)
    for i in range(1 << m):
        # Check current combination
        current = [0] * n
        press_count = 0
        
        # Calculate sum
        for b_idx in range(m):
            if (i >> b_idx) & 1:
                press_count += 1
                vec = button_vecs[b_idx]
                for k in range(n):
                    current[k] ^= vec[k]
        
        if current == target:
            if press_count < min_presses:
                min_presses = press_count
                
    return min_presses if min_presses != float('inf') else 0 # Should we return 0 or inf? Problem implies solvable.

def solve_part2_machine(machine):
    # Ax = J
    # A cols are buttons. Rows are dimensions.
    target = machine['joltages']
    n = len(target)
    buttons = machine['buttons']
    m = len(buttons)
    
    # Build Matrix A (n x m)
    # n rows (constraints), m cols (variables)
    A = [[0] * m for _ in range(n)]
    for col, b_indices in enumerate(buttons):
        for row in b_indices:
            if row < n:
                A[row][col] = 1
                
    # Augmented Matrix [A | J]
    # Use Fraction for exact arithmetic
    matrix = []
    for r in range(n):
        row = [Fraction(x) for x in A[r]] + [Fraction(target[r])]
        matrix.append(row)
        
    # Gaussian Elimination
    pivot_row = 0
    pivots = {} # col -> row
    free_vars = []
    
    for col in range(m):
        if pivot_row >= n:
            free_vars.append(col)
            continue
            
        # Find pivot
        sel = -1
        for r in range(pivot_row, n):
            if matrix[r][col] != 0:
                sel = r
                break
        
        if sel == -1:
            free_vars.append(col)
            continue
            
        # Swap
        matrix[pivot_row], matrix[sel] = matrix[sel], matrix[pivot_row]
        
        # Normalize pivot to 1
        inv = 1 / matrix[pivot_row][col]
        for c in range(col, m + 1):
            matrix[pivot_row][c] *= inv
            
        # Eliminate others
        for r in range(n):
            if r != pivot_row and matrix[r][col] != 0:
                factor = matrix[r][col]
                for c in range(col, m + 1):
                    matrix[r][c] -= factor * matrix[pivot_row][c]
                    
        pivots[col] = pivot_row
        pivot_row += 1

    # Check consistency of remaining rows (rows with all zeros in A part must have 0 in J part)
    # consistency checked implicitly during search or explicit here?
    for r in range(pivot_row, n):
        if matrix[r][m] != 0:
            return float('inf') # Impossible
            
    # Solve
    # x_pivot = value - sum(coeff * x_free)
    
    # Determine bounds for free variables
    # x_j <= min(target[i]) since buttons add positive values. 
    # Global bound for any var x_j is min(target[i] for i affected by button j)
    # If button j affects no counters (empty column), x_j should be 0 (optimal)
    
    bounds = []
    for f in free_vars:
        # Check original column in A (not reduced)
        affected_indices = buttons[f]
        if not affected_indices:
            bounds.append(0)
            continue
            
        m_val = float('inf')
        for row_idx in affected_indices:
            if row_idx < n:
                m_val = min(m_val, target[row_idx])
        bounds.append(m_val)
        
    # Iterate free vars
    # Since we want to MINIMIZE sum(x), and A>=0, x>=0
    # Maybe iterate small to large?
    # Actually, we don't know the relation for pivot vars.
    # Pivot vars could depend positively or negatively in the reduced form.
    # But in original problem, everything is positive.
    
    ranges = [range(b + 1) for b in bounds]
    min_total = float('inf')
    
    for free_vals in product(*ranges):
        # Calculate pivot variables
        # matrix[r][col] is 1 for pivot.
        # x_pivot + sum(matrix[r][free] * x_free) = matrix[r][end]
        # x_pivot = matrix[r][end] - sum(...)
        
        current_x = {}
        # Set free vars
        for i, f in enumerate(free_vars):
            current_x[f] = Fraction(free_vals[i])
            
        possible = True
        temp_sum = sum(free_vals)
        
        # Calculate pivots
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
    print("--- Running Tests ---")
    examples = [
        "[.##.] (3) (1,3) (2) (2,3) (0,2) (0,1) {3,5,4,7}",
        "[...#.] (0,2,3,4) (2,3) (0,4) (0,1,2) (1,2,3,4) {7,5,12,7,2}",
        "[.###.#] (0,1,2,3,4) (0,3,4) (0,1,2,4,5) (1,2) {10,11,11,5,10,5}"
    ]
    
    parsed_examples = [parse_line(l) for l in examples]
    
    # Part 1 Verification
    print("Verifying Part 1 Examples...")
    p1_expected = [2, 3, 2]
    p1_total_expected = 7
    
    p1_total = 0
    for i, m in enumerate(parsed_examples):
        res = solve_part1_machine(m)
        print(f"  Ex {i+1}: Output {res}, Expected {p1_expected[i]}")
        assert res == p1_expected[i], f"Part 1 Ex {i+1} Failed: Got {res}, Expected {p1_expected[i]}"
        p1_total += res
        
    assert p1_total == p1_total_expected
    print("✅ Part 1 Tests Passed!")

    # Part 2 Verification
    print("Verifying Part 2 Examples...")
    p2_expected = [10, 12, 11]
    p2_total_expected = 33
    
    p2_total = 0
    for i, m in enumerate(parsed_examples):
        res = solve_part2_machine(m)
        print(f"  Ex {i+1}: Output {res}, Expected {p2_expected[i]}")
        assert res == p2_expected[i], f"Part 2 Ex {i+1} Failed: Got {res}, Expected {p2_expected[i]}"
        p2_total += res
        
    assert p2_total == p2_total_expected
    print("✅ Part 2 Tests Passed!")
    print("---------------------")

def main():
    run_tests()
    
    print("Processing Input File...")
    with open('input-day10.txt', 'r') as f:
        lines = f.readlines()
        
    parsed = [parse_line(l.strip()) for l in lines if l.strip()]
    
    # Part 1
    total_p1 = 0
    for i, m in enumerate(parsed):
        if not m: continue
        res = solve_part1_machine(m)
        total_p1 += res
        if i < 3:
            print(f"Machine {i+1} P1: {res}")
            
    print(f"Part 1 Total: {total_p1}")
    
    # Part 2
    total_p2 = 0
    for i, m in enumerate(parsed):
        if not m: continue
        res = solve_part2_machine(m)
        total_p2 += res
        if i < 3:
            print(f"Machine {i+1} P2: {res}")
            
    print(f"Part 2 Total: {total_p2}")

if __name__ == '__main__':
    main()
