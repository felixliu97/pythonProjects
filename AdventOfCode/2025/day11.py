import sys
from collections import defaultdict

def parse_input(filename):
    adj = defaultdict(list)
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(':')
                src = parts[0].strip()
                dests = parts[1].strip().split()
                adj[src].extend(dests)
    except FileNotFoundError:
        print(f"Error: File {filename} not found.")
        sys.exit(1)
    return adj

def count_paths(node, target, adj, memo):
    if node == target:
        return 1
    if node in memo:
        return memo[node]
    
    total_paths = 0
    if node in adj:
        for neighbor in adj[node]:
            total_paths += count_paths(neighbor, target, adj, memo)
    
    memo[node] = total_paths
    return total_paths

def run_tests():
    print("Running tests...")
    # Example 1
    test_adj = {
        'aaa': ['you', 'hhh'], 'you': ['bbb', 'ccc'], 'bbb': ['ddd', 'eee'],
        'ccc': ['ddd', 'eee', 'fff'], 'ddd': ['ggg'], 'eee': ['out'],
        'fff': ['out'], 'ggg': ['out'], 'hhh': ['ccc', 'fff', 'iii'], 'iii': ['out']
    }
    memo = {}
    
    print("Verifying Part 1 Example...")
    res = count_paths('you', 'out', test_adj, memo)
    expected = 5
    if res == expected:
        print(f"✅ Part 1 Example Passed")
    else:
        print(f"❌ Part 1 Example Failed: Expected {expected}, Got {res}")

    # Example 2
    test_adj_p2 = {
        'svr': ['aaa', 'bbb'], 'aaa': ['fft'], 'fft': ['ccc'], 'bbb': ['tty'],
        'tty': ['ccc'], 'ccc': ['ddd', 'eee'], 'ddd': ['hub'], 'hub': ['fff'],
        'eee': ['dac'], 'dac': ['fff'], 'fff': ['ggg', 'hhh'], 'ggg': ['out'],
        'hhh': ['out']
    }
    
    # Path 1: svr -> dac -> fft -> out
    memo1 = {}; s1 = count_paths('svr', 'dac', test_adj_p2, memo1)
    memo2 = {}; s2 = count_paths('dac', 'fft', test_adj_p2, memo2)
    memo3 = {}; s3 = count_paths('fft', 'out', test_adj_p2, memo3)
    p1 = s1 * s2 * s3
    
    # Path 2: svr -> fft -> dac -> out
    memo4 = {}; s4 = count_paths('svr', 'fft', test_adj_p2, memo4)
    memo5 = {}; s5 = count_paths('fft', 'dac', test_adj_p2, memo5)
    memo6 = {}; s6 = count_paths('dac', 'out', test_adj_p2, memo6)
    p2 = s4 * s5 * s6
    
    print("Verifying Part 2 Example...")
    expected_p2 = 2
    actual_p2 = p1 + p2
    if actual_p2 == expected_p2:
        print(f"✅ Part 2 Example Passed")
    else:
        print(f"❌ Part 2 Example Failed: Expected {expected_p2}, Got {actual_p2}")
        
    print("✅ Tests completed!")

def solve_part1():
    print("--- Part 1 ---")
    filename = 'input-day11.txt'
    adj = parse_input(filename)
    start_node = 'you'
    target_node = 'out'
    if start_node in adj or any(start_node in adj[x] for x in adj):
        memo = {}
        result = count_paths(start_node, target_node, adj, memo)
        print(f"Result: {result}")
    else:
        print(f"Node '{start_node}' not found in graph.")

def solve_part2():
    print("--- Part 2 ---")
    filename = 'input-day11.txt'
    adj = parse_input(filename)
    start_node = 'svr'
    target_node = 'out'
    nodes_to_visit = ['dac', 'fft']
    
    # Path 1: svr -> dac -> fft -> out
    memo1 = {}
    p1_segment1 = count_paths('svr', 'dac', adj, memo1)
    memo2 = {}
    p1_segment2 = count_paths('dac', 'fft', adj, memo2)
    memo3 = {}
    p1_segment3 = count_paths('fft', 'out', adj, memo3)
    path1_total = p1_segment1 * p1_segment2 * p1_segment3

    # Path 2: svr -> fft -> dac -> out
    memo4 = {}
    p2_segment1 = count_paths('svr', 'fft', adj, memo4)
    memo5 = {}
    p2_segment2 = count_paths('fft', 'dac', adj, memo5)
    memo6 = {}
    p2_segment3 = count_paths('dac', 'out', adj, memo6)
    path2_total = p2_segment1 * p2_segment2 * p2_segment3
    
    total_part2 = path1_total + path2_total
    print(f"Result: {total_part2}")

if __name__ == '__main__':
    run_tests()
    solve_part1()
    solve_part2()
