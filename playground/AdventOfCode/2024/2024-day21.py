import sys
from functools import lru_cache
from itertools import permutations

# Keypad Layouts
NUM_KEYPAD = {
    '7': (0, 0), '8': (0, 1), '9': (0, 2),
    '4': (1, 0), '5': (1, 1), '6': (1, 2),
    '1': (2, 0), '2': (2, 1), '3': (2, 2),
                 '0': (3, 1), 'A': (3, 2)
}
NUM_GAP = (3, 0)

DIR_KEYPAD = {
                 '^': (0, 1), 'A': (0, 2),
    '<': (1, 0), 'v': (1, 1), '>': (1, 2)
}
DIR_GAP = (0, 0)

GAP_POS = {
    'num': NUM_GAP,
    'dir': DIR_GAP
}
KEYPADS = {
    'num': NUM_KEYPAD,
    'dir': DIR_KEYPAD
}

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            real_codes = [line.strip() for line in f if line.strip()]
        return real_codes
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def run_tests():
    print("Running tests...")
    
    # Example Codes
    codes = ["029A", "980A", "179A", "456A", "379A"]
    total_complexity = 0
    
    for code in codes:
        complexity = solve_code(code, num_robots=2)
        print(f"Test Code {code}: Complexity {complexity}")
        total_complexity += complexity
        
    print(f"Test Total Example Complexity: {total_complexity} (Exp: 126384)")
    expected_complexity = 126384
    if total_complexity == expected_complexity:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_complexity}, Got {total_complexity}")
        
    print("✅ Tests completed!")

def get_sequences(start_pos, end_pos, gap_pos):
    sr, sc = start_pos
    er, ec = end_pos
    dr, dc = er - sr, ec - sc
    
    moves = []
    if dr > 0: moves.extend(['v'] * abs(dr))
    elif dr < 0: moves.extend(['^'] * abs(dr))
    if dc > 0: moves.extend(['>'] * abs(dc))
    elif dc < 0: moves.extend(['<'] * abs(dc))
    
    valid_seqs = set()
    for p in set(permutations(moves)):
        # Check if hitting gap
        cr, cc = sr, sc
        valid = True
        for move in p:
            if move == '^': cr -= 1
            elif move == 'v': cr += 1
            elif move == '<': cc -= 1
            elif move == '>': cc += 1
            
            if (cr, cc) == gap_pos:
                valid = False
                break
        
        if valid:
            valid_seqs.add("".join(p) + "A")
            
    return list(valid_seqs)

@lru_cache(None)
def get_path_cost(start_key, end_key, depth, is_num_pad):
    keypad = KEYPADS['num'] if is_num_pad else KEYPADS['dir']
    gap = GAP_POS['num'] if is_num_pad else GAP_POS['dir']
    
    start_pos = keypad[start_key]
    end_pos = keypad[end_key]
    
    paths = get_sequences(start_pos, end_pos, gap)
    
    if depth == 0:
        return len(paths[0])
    
    best_cost = float('inf')
    for path in paths:
        current_cost = 0
        current_key = 'A'
        for char in path:
            current_cost += get_path_cost(current_key, char, depth - 1, False)
            current_key = char
        best_cost = min(best_cost, current_cost)
        
    return best_cost

def solve_code(code, num_robots=2):
    total_cost = 0
    current_key = 'A'
    for char in code:
        total_cost += get_path_cost(current_key, char, num_robots, True)
        current_key = char
        
    numeric_part = int(code[:-1].lstrip('0') or '0')
    return total_cost * numeric_part

def solve_part1():
    print("--- Part 1 ---")
    real_codes = parse_input("2024-day21.txt")
    real_total = 0
    for code in real_codes:
        real_total += solve_code(code, num_robots=2)
    print(f"Result: {real_total}")

def solve_part2():
    print("--- Part 2 ---")
    real_codes = parse_input("2024-day21.txt")
    part2_total = 0
    for code in real_codes:
        part2_total += solve_code(code, num_robots=25)
    print(f"Result: {part2_total}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
