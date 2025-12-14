import sys
from collections import Counter

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

# Card mappings
ORDER_P1 = "23456789TJQKA"
ORDER_P2 = "J23456789TQKA"

def get_hand_type(hand, part2=False):
    # Returns rank 0-6 (High Card to Five of a Kind)
    counts = Counter(hand)
    
    if part2 and 'J' in counts:
        j_count = counts['J']
        del counts['J']
        
        # Add J to the most frequent card
        if not counts:
            # All Js
            counts['A'] = 5
        else:
            most_common = counts.most_common(1)[0][0]
            counts[most_common] += j_count
            
    # Normalize counts to list of values
    shape = sorted(counts.values(), reverse=True)
    
    if shape == [5]: return 6 # Five of a Kind
    if shape == [4, 1]: return 5 # Four of a Kind
    if shape == [3, 2]: return 4 # Full House
    if shape == [3, 1, 1]: return 3 # Three of a Kind
    if shape == [2, 2, 1]: return 2 # Two Pair
    if shape == [2, 1, 1, 1]: return 1 # One Pair
    return 0 # High Card

def hand_strength(item, part2=False):
    hand, bid = item
    type_score = get_hand_type(hand, part2)
    order = ORDER_P2 if part2 else ORDER_P1
    
    # Create list of card values
    card_scores = [order.index(c) for c in hand]
    
    return (type_score, card_scores)

def solve(data):
    lines = data.split('\n')
    hands = []
    for line in lines:
        h, b = line.split()
        hands.append((h, int(b)))
        
    # Part 1
    hands.sort(key=lambda x: hand_strength(x, part2=False))
    p1 = 0
    for i, (h, b) in enumerate(hands):
        p1 += b * (i + 1)
        
    # Part 2
    hands.sort(key=lambda x: hand_strength(x, part2=True))
    p2 = 0
    for i, (h, b) in enumerate(hands):
        p2 += b * (i + 1)
        
    return p1, p2

def run_tests():
    print("Running tests...")
    example = """32T3K 765
T55J5 684
KK677 28
KTJJT 220
QQQJA 483"""
    
    p1, p2 = solve(example)
    expected_p1 = 6440
    expected_p2 = 5905
    
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
    data = parse_input("2023-day7.txt")
    p1, p2 = solve(data)
    print("--- Part 1 ---")
    print(f"Result: {p1}")
    print("--- Part 2 ---")
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1_and_2()
