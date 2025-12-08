import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            content = f.read().strip()
    except FileNotFoundError:
        return [], []

    if not content:
        return [], []

    parts = content.split('\n\n')
    patterns = parts[0].split(', ')
    designs = parts[1].split('\n')
    return patterns, designs

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

def solve():
    # Example Verification
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
            
    print(f"Example Part 1: {part1_count}")
    print(f"Example Part 2: {part2_total}")
    assert part1_count == 6, f"Expected 6, got {part1_count}"
    assert part2_total == 16, f"Expected 16, got {part2_total}"

    # Real Input
    patterns, designs = parse_input('input-day19.txt')
    if not patterns:
        print("Input file not found or empty.")
        return

    patterns_set = set(patterns)
    max_len = max(len(p) for p in patterns)
    
    memo = {}
    part1_count = 0
    part2_total = 0
    
    for design in designs:
        ways = count_ways(design, patterns_set, max_len, memo)
        if ways > 0:
            part1_count += 1
        part2_total += ways
            
    print(f"Part 1 Count: {part1_count}")
    print(f"Part 2 Total: {part2_total}")

if __name__ == '__main__':
    # Increase recursion limit just in case, though DP usually avoids deep recursion if done bottom up? 
    # But this is top-down. String slicing is fine.
    sys.setrecursionlimit(20000)
    solve()
