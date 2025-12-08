from functools import cmp_to_key

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            content = f.read().strip()
        
        parts = content.split('\n\n')
        rules_lines = parts[0].strip().split('\n')
        updates_lines = parts[1].strip().split('\n')
        
        # Parse rules into a set of tuples (X, Y) meaning X must be before Y
        rules = set()
        for line in rules_lines:
            x, y = map(int, line.split('|'))
            rules.add((x, y))
            
        # Parse updates into list of lists
        updates = []
        for line in updates_lines:
            updates.append(list(map(int, line.split(','))))
            
        return rules, updates
    except FileNotFoundError:
        print(f"Error: File {filename} not found.")
        return set(), []

def is_ordered(update, rules):
    # Check every pair of pages in the update
    n = len(update)
    for i in range(n):
        for j in range(i + 1, n):
            # If update[j] should be before update[i], then it's unordered
            if (update[j], update[i]) in rules:
                return False
    return True

def compare_pages(a, b, rules):
    if (a, b) in rules:
        return -1 # a comes before b
    elif (b, a) in rules:
        return 1 # b comes before a
    else:
        return 0

def solve(filename):
    rules, updates = parse_input(filename)
    part1_sum = 0
    part2_sum = 0
    
    comparator = cmp_to_key(lambda a, b: compare_pages(a, b, rules))
    
    for update in updates:
        if is_ordered(update, rules):
            middle_index = len(update) // 2
            part1_sum += update[middle_index]
        else:
            # It's unordered, so we sort it for Part 2
            sorted_update = sorted(update, key=comparator)
            middle_index = len(sorted_update) // 2
            part2_sum += sorted_update[middle_index]
            
    return part1_sum, part2_sum

def test():
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
        
    p1 = 0
    p2 = 0
    comparator = cmp_to_key(lambda a, b: compare_pages(a, b, rules))

    for update in updates:
        if is_ordered(update, rules):
            p1 += update[len(update) // 2]
        else:
            sorted_update = sorted(update, key=comparator)
            p2 += sorted_update[len(sorted_update) // 2]
            
    print(f"Test Part 1: {p1}")
    assert p1 == 143, f"Expected 143, got {p1}"
    
    print(f"Test Part 2: {p2}")
    assert p2 == 123, f"Expected 123, got {p2}"

if __name__ == "__main__":
    test()
    print("Tests passed!")
    p1_result, p2_result = solve("input-day5.txt")
    print(f"Part 1 Result: {p1_result}")
    print(f"Part 2 Result: {p2_result}")
