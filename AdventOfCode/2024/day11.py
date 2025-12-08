from collections import Counter

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            data = f.read().strip()
            return [int(x) for x in data.split()]
    except FileNotFoundError:
        print(f"Error: File {filename} not found.")
        return []

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

def solve(filename):
    stones = parse_input(filename)
    if not stones:
        return 0, 0
        
    stone_counts = Counter(stones)
    
    # Part 1: 25 Blinks
    for _ in range(25):
        stone_counts = blink(stone_counts)
    part1_result = sum(stone_counts.values())
    
    # Part 2: Continue to 75 Blinks (25 + 50)
    for _ in range(50):
        stone_counts = blink(stone_counts)
    part2_result = sum(stone_counts.values())
        
    return part1_result, part2_result

def test():
    # Only test part 1 logic here as Part 2 is just more iterations
    initial_stones = [125, 17]
    stone_counts = Counter(initial_stones)
    for _ in range(25):
        stone_counts = blink(stone_counts)
    assert sum(stone_counts.values()) == 55312

if __name__ == "__main__":
    test()
    print("Tests passed!")
    p1, p2 = solve("input-day11.txt")
    print(f"Part 1 Result: {p1}")
    print(f"Part 2 Result: {p2}")
