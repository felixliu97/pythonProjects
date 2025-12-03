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
        # We need to pick k - i digits total (including this one).
        # So we need to leave k - i - 1 digits after this one.
        # The last possible index for this digit is n - (k - i).
        # In python slice notation (exclusive end), it's n - (k - i) + 1.
        remaining_needed = k - i
        search_end = n - remaining_needed + 1
        
        # Find max digit in the valid window
        # We want the first occurrence of the max digit to maximize opportunities for next steps
        # (though strictly for lexicographical max, any occurrence of the same max digit 
        # that leaves enough space is fine, but picking the earliest is safe/standard greedy).
        # Actually, picking the earliest max digit is optimal because it leaves the largest 
        # possible suffix for the remaining choices.
        
        window = digits[current_idx : search_end]
        max_digit = -1
        max_digit_rel_idx = -1
        
        for idx, digit in enumerate(window):
            if digit > max_digit:
                max_digit = digit
                max_digit_rel_idx = idx
            if digit == 9: # Optimization: 9 is the max possible, take it immediately
                break
        
        result.append(max_digit)
        current_idx += max_digit_rel_idx + 1
        
    # Convert list of digits to integer
    val = 0
    for d in result:
        val = val * 10 + d
    return val

def solve():
    try:
        with open('input-day3.txt', 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("Error: input-day3.txt not found.")
        return

    total_joltage_p1 = 0
    total_joltage_p2 = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        digits = [int(c) for c in line if c.isdigit()]
        
        # Part 1: k=2
        total_joltage_p1 += find_max_subsequence(digits, 2)
        
        # Part 2: k=12
        total_joltage_p2 += find_max_subsequence(digits, 12)

    print(f"Part 1 Total: {total_joltage_p1}")
    print(f"Part 2 Total: {total_joltage_p2}")

def test_examples():
    examples_p1 = [
        ("987654321111111", 98),
        ("811111111111119", 89),
        ("234234234234278", 78),
        ("818181911112111", 92)
    ]
    
    print("Testing Part 1 Examples:")
    for line, expected in examples_p1:
        digits = [int(c) for c in line]
        got = find_max_subsequence(digits, 2)
        print(f"Input: {line}, Expected: {expected}, Got: {got}, Pass: {got == expected}")

    examples_p2 = [
        ("987654321111111", 987654321111),
        ("811111111111119", 811111111119),
        ("234234234234278", 434234234278),
        ("818181911112111", 888911112111)
    ]
    
    print("\nTesting Part 2 Examples:")
    for line, expected in examples_p2:
        digits = [int(c) for c in line]
        got = find_max_subsequence(digits, 12)
        print(f"Input: {line}, Expected: {expected}, Got: {got}, Pass: {got == expected}")

if __name__ == "__main__":
    print("Running examples...")
    test_examples()
    print("\nRunning solution...")
    solve()
