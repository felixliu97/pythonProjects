import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            content = f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

    if not content:
        return [], []

    parts = content.split('\n\n')
    patterns = parts[0].split(', ')
    designs = parts[1].split('\n')
    return patterns, designs

def run_tests():
    print("Running tests...")
    
    example_patterns_str = "r, wr, b, g, bwu, rb, gb, br"
    example_designs_str = """brwrr
bggr
gbbr
rrbgbr
ubwu
bwurrg
brgr
bbrgwb"""
    
    ex_patterns = example_patterns_str.split(', ')
    ex_designs = example_designs_str.split('\n')
    
    ex_patterns_set = set(ex_patterns)
    ex_max_len = max(len(p) for p in ex_patterns)
    
    part1_count = 0
    part2_total = 0
    memo = {}
    for design in ex_designs:
        ways = count_ways(design, ex_patterns_set, ex_max_len, memo)
        if ways > 0:
            part1_count += 1
        part2_total += ways
            
    print(f"Test Part 1 Count: {part1_count} (Exp: 6)")
    expected_p1 = 6
    if part1_count == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {part1_count}")
        
    print(f"Test Part 2 Total: {part2_total} (Exp: 16)")
    expected_p2 = 16
    if part2_total == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {part2_total}")
        
    print("✅ Tests completed!")

def count_ways(design, patterns_set, max_len, memo):
    if design in memo:
        return memo[design]
    
    if not design:
        return 1
    
    total_ways = 0
    limit = min(len(design), max_len)
    
    for i in range(limit, 0, -1):
        prefix = design[:i]
        if prefix in patterns_set:
            ways = count_ways(design[i:], patterns_set, max_len, memo)
            total_ways += ways
    
    memo[design] = total_ways
    return total_ways

def solve_part1():
    print("--- Part 1 ---")
    patterns, designs = parse_input("2024-day19.txt")
    if not patterns: return
    
    patterns_set = set(patterns)
    max_len = max(len(p) for p in patterns)
    memo = {}
    part1_count = 0
    
    for design in designs:
        if count_ways(design, patterns_set, max_len, memo) > 0:
            part1_count += 1
            
    print(f"Result: {part1_count}")

def solve_part2():
    print("--- Part 2 ---")
    patterns, designs = parse_input("2024-day19.txt")
    if not patterns: return
    
    patterns_set = set(patterns)
    max_len = max(len(p) for p in patterns)
    memo = {}
    part2_total = 0
    
    for design in designs:
        part2_total += count_ways(design, patterns_set, max_len, memo)
            
    print(f"Result: {part2_total}")

if __name__ == "__main__":
    sys.setrecursionlimit(20000)
    run_tests()
    solve_part1()
    solve_part2()
