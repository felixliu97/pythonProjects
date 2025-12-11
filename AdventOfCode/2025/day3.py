import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        return [line.strip() for line in lines if line.strip()]
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def find_max_subsequence(digits, k):
    """
    Finds the lexicographically largest subsequence of length k.
    """
    n = len(digits)
    if k > n:
        return 0
    
    result = []
    current_idx = 0
    for i in range(k):
        remaining_needed = k - i
        search_end = n - remaining_needed + 1
        
        window = digits[current_idx : search_end]
        max_digit = -1
        max_digit_rel_idx = -1
        
        for idx, digit in enumerate(window):
            if digit > max_digit:
                max_digit = digit
                max_digit_rel_idx = idx
            if digit == 9: 
                break
        
        result.append(max_digit)
        current_idx += max_digit_rel_idx + 1
        
    val = 0
    for d in result:
        val = val * 10 + d
    return val

def run_tests():
    print("Running tests...")
    
    # Part 1 Tests
    examples_p1 = [
        ("987654321111111", 98),
        ("811111111111119", 89),
        ("234234234234278", 78),
        ("818181911112111", 92)
    ]
    
    print("Verifying Part 1 Examples...")
    for line, expected in examples_p1:
        digits = [int(c) for c in line]
        got = find_max_subsequence(digits, 2)
        if got == expected:
            print(f"✅ Input: {line} -> Passed")
        else:
            print(f"❌ Input: {line} -> Failed (Expected {expected}, Got {got})")
            
    # Part 2 Tests
    examples_p2 = [
        ("987654321111111", 987654321111),
        ("811111111111119", 811111111119),
        ("234234234234278", 434234234278),
        ("818181911112111", 888911112111)
    ]
    
    print("Verifying Part 2 Examples...")
    for line, expected in examples_p2:
        digits = [int(c) for c in line]
        got = find_max_subsequence(digits, 12)
        if got == expected:
            print(f"✅ Input: {line} -> Passed")
        else:
            print(f"❌ Input: {line} -> Failed (Expected {expected}, Got {got})")
            
    print("✅ Tests completed!")

def solve_part1():
    print("--- Part 1 ---")
    lines = parse_input('input-day3.txt')
    total_joltage_p1 = 0
    for line in lines:
        digits = [int(c) for c in line if c.isdigit()]
        total_joltage_p1 += find_max_subsequence(digits, 2)
    print(f"Total: {total_joltage_p1}")

def solve_part2():
    print("--- Part 2 ---")
    lines = parse_input('input-day3.txt')
    total_joltage_p2 = 0
    for line in lines:
        digits = [int(c) for c in line if c.isdigit()]
        total_joltage_p2 += find_max_subsequence(digits, 12)
    print(f"Total: {total_joltage_p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
