import sys
from collections import Counter

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            content = f.read()
        
        left_list = []
        right_list = []
        
        for line in content.strip().split('\n'):
            parts = line.strip().split()
            if len(parts) >= 2:
                left_list.append(int(parts[0]))
                right_list.append(int(parts[1]))
                
        return left_list, right_list
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def run_tests():
    print("Running tests...")
    
    example_input = """3   4
4   3
2   5
1   3
3   9
3   3"""
    
    # Parse example
    left_list = []
    right_list = []
    for line in example_input.strip().split('\n'):
        parts = line.strip().split()
        if len(parts) >= 2:
            left_list.append(int(parts[0]))
            right_list.append(int(parts[1]))
            
    # Test Part 1
    # Pair up and sum distances
    l_sorted = sorted(left_list)
    r_sorted = sorted(right_list)
    dist = sum(abs(l - r) for l, r in zip(l_sorted, r_sorted))
    
    print(f"Test Part 1 Result: {dist} (Expected 11)")
    expected_p1 = 11
    if dist == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {dist}")

    # Test Part 2
    # Similarity score
    right_counts = Counter(right_list)
    similarity = sum(num * right_counts[num] for num in left_list)
    
    print(f"Test Part 2 Result: {similarity} (Expected 31)")
    expected_p2 = 31
    if similarity == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {similarity}")
        
    print("✅ Tests completed!")

def solve_part1():
    print("--- Part 1 ---")
    left_list, right_list = parse_input("input-day1.txt")
    
    left_list.sort()
    right_list.sort()
    
    total_distance = sum(abs(l - r) for l, r in zip(left_list, right_list))
    print(f"Result: {total_distance}")

def solve_part2():
    print("--- Part 2 ---")
    left_list, right_list = parse_input("input-day1.txt")
    
    right_counts = Counter(right_list)
    similarity_score = sum(num * right_counts[num] for num in left_list)
    print(f"Result: {similarity_score}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
