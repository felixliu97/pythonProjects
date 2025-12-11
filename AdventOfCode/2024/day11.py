import sys
from collections import Counter

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            data = f.read().strip()
            return [int(x) for x in data.split()]
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def run_tests():
    print("Running tests...")
    
    initial_stones = [125, 17]
    stone_counts = Counter(initial_stones)
    
    # Part 1 Example (25 blinks)
    final_counts = solve_logic(stone_counts, 25)
    result = sum(final_counts.values())
    expected = 55312
    
    print(f"Test Part 1 (25 blinks): {result}")
    
    if result == expected:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected}, Got {result}")
        
    print("✅ Tests completed!")

def blink(stone_counts):
    new_counts = Counter()
    
    for val, count in stone_counts.items():
        if val == 0:
            new_counts[1] += count
        else:
            s_val = str(val)
            if len(s_val) % 2 == 0:
                mid = len(s_val) // 2
                left = int(s_val[:mid])
                right = int(s_val[mid:])
                new_counts[left] += count
                new_counts[right] += count
            else:
                new_counts[val * 2024] += count
                
    return new_counts

def solve_logic(initial_counts, blinks):
    stone_counts = initial_counts.copy()
    for _ in range(blinks):
        stone_counts = blink(stone_counts)
    return stone_counts

def solve_part1():
    print("--- Part 1 ---")
    stones = parse_input("input-day11.txt")
    if not stones: return
    
    stone_counts = Counter(stones)
    final_counts = solve_logic(stone_counts, 25)
    print(f"Result: {sum(final_counts.values())}")

def solve_part2():
    print("--- Part 2 ---")
    stones = parse_input("input-day11.txt")
    if not stones: return
    
    stone_counts = Counter(stones)
    final_counts = solve_logic(stone_counts, 75)
    print(f"Result: {sum(final_counts.values())}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
