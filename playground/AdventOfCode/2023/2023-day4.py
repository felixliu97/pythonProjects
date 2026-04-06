import sys
import re

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def solve(data):
    lines = data.split('\n')
    
    total_points = 0
    # For Part 2: card_counts[i] = number of copies of card i+1
    card_counts = [1] * len(lines)
    
    for i, line in enumerate(lines):
        # Card 1: 41 48 83 86 17 | 83 86  6 31 17  9 48 53
        parts = line.split(':')[1].split('|')
        winning = set(map(int, parts[0].split()))
        have = set(map(int, parts[1].split()))
        
        matches = len(winning & have)
        
        # Part 1
        if matches > 0:
            total_points += 2 ** (matches - 1)
            
        # Part 2
        # You win copies of the next <matches> cards
        current_card_count = card_counts[i]
        for j in range(matches):
            if i + 1 + j < len(lines):
                card_counts[i + 1 + j] += current_card_count
                
    total_cards = sum(card_counts)
    return total_points, total_cards

def run_tests():
    print("Running tests...")
    example = """Card 1: 41 48 83 86 17 | 83 86  6 31 17  9 48 53
Card 2: 13 32 20 16 61 | 61 30 68 82 17 32 24 19
Card 3:  1 21 53 59 44 | 69 82 63 72 16 21 14  1
Card 4: 41 92 73 84 69 | 59 84 76 51 58  5 54 83
Card 5: 87 83 26 28 32 | 88 30 70 12 93 22 82 36
Card 6: 31 18 13 56 72 | 74 77 10 23 35 67 36 11"""
    
    p1, p2 = solve(example)
    expected_p1 = 13
    expected_p2 = 30
    
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
    data = parse_input("2023-day4.txt")
    p1, p2 = solve(data)
    print("--- Part 1 ---")
    print(f"Result: {p1}")
    print("--- Part 2 ---")
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1_and_2()
