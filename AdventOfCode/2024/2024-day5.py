import sys
from functools import cmp_to_key

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            content = f.read().strip()
        
        parts = content.split('\n\n')
        rules_lines = parts[0].strip().split('\n')
        updates_lines = parts[1].strip().split('\n')
        
        rules = set()
        for line in rules_lines:
            x, y = map(int, line.split('|'))
            rules.add((x, y))
            
        updates = []
        for line in updates_lines:
            updates.append(list(map(int, line.split(','))))
            
        return rules, updates
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def run_tests():
    print("Running tests...")
    
    example_rules = [
        "47|53", "97|13", "97|61", "97|47", "75|29", "61|13", "75|53", "29|13", 
        "97|29", "53|29", "61|53", "97|53", "61|29", "47|13", "75|47", "97|75", 
        "47|61", "75|61", "47|29", "75|13", "53|13"
    ]
    example_updates = [
        "75,47,61,53,29",
        "97,61,53,29,13",
        "75,29,13",
        "75,97,47,61,53",
        "61,13,29",
        "97,13,75,29,47"
    ]
    
    rules = set()
    for r in example_rules:
        x, y = map(int, r.split('|'))
        rules.add((x, y))
        
    updates = []
    for u in example_updates:
        updates.append(list(map(int, u.split(','))))
        
    p1, p2 = solve_logic(rules, updates)
    
    expected_p1 = 143
    if p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1}")

    expected_p2 = 123
    if p2 == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {p2}")
    
    print("✅ Tests completed!")

def is_ordered(update, rules):
    n = len(update)
    for i in range(n):
        for j in range(i + 1, n):
            if (update[j], update[i]) in rules:
                return False
    return True

def compare_pages(a, b, rules):
    if (a, b) in rules:
        return -1 
    elif (b, a) in rules:
        return 1 
    else:
        return 0

def solve_logic(rules, updates):
    part1_sum = 0
    part2_sum = 0
    comparator = cmp_to_key(lambda a, b: compare_pages(a, b, rules))
    
    for update in updates:
        if is_ordered(update, rules):
            middle_index = len(update) // 2
            part1_sum += update[middle_index]
        else:
            sorted_update = sorted(update, key=comparator)
            middle_index = len(sorted_update) // 2
            part2_sum += sorted_update[middle_index]
            
    return part1_sum, part2_sum

def solve_part1():
    print("--- Part 1 ---")
    rules, updates = parse_input("2024-day5.txt")
    p1, _ = solve_logic(rules, updates)
    print(f"Result: {p1}")

def solve_part2():
    print("--- Part 2 ---")
    rules, updates = parse_input("2024-day5.txt")
    _, p2 = solve_logic(rules, updates)
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
