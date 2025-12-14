import sys
import functools

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

@functools.lru_cache(maxsize=None)
def count_arrangements(conditions, rules):
    # conditions: string like "???.###"
    # rules: tuple of ints like (1, 1, 3)
    
    if not rules:
        # If no more rules, valid only if no '#' left
        if '#' in conditions:
            return 0
        return 1
    
    if not conditions:
        return 0
    
    # Analyze first char
    total = 0
    char = conditions[0]
    next_conditions = conditions[1:]
    
    # Case 1: Treat as '.'
    if char in '.?':
        total += count_arrangements(next_conditions, rules)
        
    # Case 2: Treat as '#'
    if char in '#?':
        # Must match rule
        current_rule = rules[0]
        # Need current_rule chars to be potentially '#'
        if len(conditions) >= current_rule:
             # Check if the block fits (no '.')
            block = conditions[:current_rule]
            if '.' not in block:
                # Check next char (must be '.' or end of string)
                if len(conditions) == current_rule:
                    # Fits exactly at end
                    total += count_arrangements("", rules[1:])
                elif conditions[current_rule] != '#':
                    # Must be followed by separator ('.' or '?')
                    # Skip the separator too
                    total += count_arrangements(conditions[current_rule+1:], rules[1:])
                    
    return total

def solve(data):
    lines = data.split('\n')
    total_p1 = 0
    total_p2 = 0
    
    for line in lines:
        parts = line.split()
        conditions = parts[0]
        rules = tuple(map(int, parts[1].split(',')))
        
        # Part 1
        total_p1 += count_arrangements(conditions, rules)
        
        # Part 2
        # Unfold
        unfolded_conditions = "?".join([conditions] * 5)
        unfolded_rules = rules * 5
        total_p2 += count_arrangements(unfolded_conditions, unfolded_rules)
        
    return total_p1, total_p2

def run_tests():
    print("Running tests...")
    example = """???.### 1,1,3
.??..??...?##. 1,1,3
?#?#?#?#?#?#?#? 1,3,1,6
????.#...#... 4,1,1
????.######..#####. 1,6,5
?###???????? 3,2,1"""
    
    p1, p2 = solve(example)
    expected_p1 = 21
    expected_p2 = 525152
    
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
    data = parse_input("2023-day12.txt")
    p1, p2 = solve(data)
    print("--- Part 1 ---")
    print(f"Result: {p1}")
    print("--- Part 2 ---")
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1_and_2()
