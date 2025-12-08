from collections import defaultdict

def evolve_secret(secret):
    # Step 1: Multiply by 64, mix, prune
    result = secret * 64
    secret = (result ^ secret) % 16777216
    
    # Step 2: Divide by 32, round down, mix, prune
    result = secret // 32
    secret = (result ^ secret) % 16777216
    
    # Step 3: Multiply by 2048, mix, prune
    result = secret * 2048
    secret = (result ^ secret) % 16777216
    
    return secret

def get_2000th_secret(initial_secret):
    secret = initial_secret
    for _ in range(2000):
        secret = evolve_secret(secret)
    return secret

def get_prices(initial_secret, count=2000):
    prices = [initial_secret % 10]
    secret = initial_secret
    for _ in range(count):
        secret = evolve_secret(secret)
        prices.append(secret % 10)
    return prices

def solve_part2(initials):
    sequence_scores = defaultdict(int)
    
    for init_val in initials:
        prices = get_prices(init_val)
        seen_sequences = set()
        # We need sequences of 4 changes.
        # Prices length is 2001 (0 to 2000).
        # Changes length is 2000.
        # Sequence windows:
        # i goes from 0 to len(prices) - 5 (inclusive)
        # because at i, we look at prices[i], i+1, i+2, i+3, i+4 (5 prices -> 4 changes)
        
        for i in range(len(prices) - 4):
            # Calculate changes
            d1 = prices[i+1] - prices[i]
            d2 = prices[i+2] - prices[i+1]
            d3 = prices[i+3] - prices[i+2]
            d4 = prices[i+4] - prices[i+3]
            
            sequence = (d1, d2, d3, d4)
            
            if sequence not in seen_sequences:
                sequence_scores[sequence] += prices[i+4]
                seen_sequences.add(sequence)
                
    return max(sequence_scores.values()) if sequence_scores else 0

def solve():
    # Example Part 1
    example_initials_p1 = [1, 10, 100, 2024]
    expected_2000th = {
        1: 8685429,
        10: 4700978,
        100: 15273692,
        2024: 8667524
    }
    
    print("--- Example Part 1 Verification ---")
    example_sum = 0
    for init_val in example_initials_p1:
        result = get_2000th_secret(init_val)
        # print(f"Initial: {init_val}, 2000th: {result} (Expected: {expected_2000th[init_val]})")
        assert result == expected_2000th[init_val]
        example_sum += result
        
    print(f"Example Part 1 Sum: {example_sum} (Expected: 37327623)")
    assert example_sum == 37327623
    print("Example Part 1 passed!")
    
    # Example Part 2
    example_initials_p2 = [1, 2, 3, 2024]
    print("\n--- Example Part 2 Verification ---")
    best_bananas = solve_part2(example_initials_p2)
    print(f"Example Part 2 Best Bananas: {best_bananas} (Expected: 23)")
    assert best_bananas == 23
    print("Example Part 2 passed!")

    # Real Input
    try:
        with open('input-day22.txt', 'r') as f:
            lines = f.readlines()
        
        real_initials = [int(line.strip()) for line in lines if line.strip()]
        
        # Part 1 Real
        total_sum = 0
        for init_val in real_initials:
            total_sum += get_2000th_secret(init_val)
        print(f"\nPart 1 Final Sum: {total_sum}")
        
        # Part 2 Real
        best_bananas_real = solve_part2(real_initials)
        print(f"Part 2 Final Best Bananas: {best_bananas_real}")
        
    except FileNotFoundError:
        print("input-day22.txt not found. Skipping real input run.")

if __name__ == '__main__':
    solve()
