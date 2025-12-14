import sys
from collections import defaultdict

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        real_initials = [int(line.strip()) for line in lines if line.strip()]
        return real_initials
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def run_tests():
    print("Running tests...")
    
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
    passed_p1 = True
    for init_val in example_initials_p1:
        result = get_2000th_secret(init_val)
        if result != expected_2000th[init_val]:
            print(f"❌ Initial {init_val}: Got {result}, Expected {expected_2000th[init_val]}")
            passed_p1 = False
        example_sum += result
        
    print(f"Test Example Part 1 Sum: {example_sum} (Exp: 37327623)")
    if example_sum == 37327623 and passed_p1:
        print("✅ Part 1 Example passed!")
    else:
        print("❌ Part 1 Example failed!")
    
    # Example Part 2
    example_initials_p2 = [1, 2, 3, 2024]
    print("\n--- Example Part 2 Verification ---")
    best_bananas = solve_logic_part2(example_initials_p2)
    print(f"Test Example Part 2 Best Bananas: {best_bananas} (Exp: 23)")
    if best_bananas == 23:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed!")
        
    print("✅ Tests completed!")

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

def solve_logic_part2(initials):
    sequence_scores = defaultdict(int)
    
    for init_val in initials:
        prices = get_prices(init_val)
        seen_sequences = set()
        
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

def solve_part1():
    print("--- Part 1 ---")
    real_initials = parse_input("2024-day22.txt")
    total_sum = 0
    for init_val in real_initials:
        total_sum += get_2000th_secret(init_val)
    print(f"Result: {total_sum}")

def solve_part2():
    print("--- Part 2 ---")
    real_initials = parse_input("2024-day22.txt")
    best_bananas = solve_logic_part2(real_initials)
    print(f"Result: {best_bananas}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
