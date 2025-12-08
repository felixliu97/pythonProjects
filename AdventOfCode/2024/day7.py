def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        equations = []
        for line in lines:
            if not line.strip(): continue
            parts = line.split(':')
            target = int(parts[0].strip())
            numbers = list(map(int, parts[1].strip().split()))
            equations.append((target, numbers))
        return equations
    except FileNotFoundError:
        print(f"Error: File {filename} not found.")
        return []

def can_solve(target, current_val, remaining_nums, enable_concat=False):
    if current_val > target:
        return False
        
    if not remaining_nums:
        return current_val == target
    
    next_num = remaining_nums[0]
    rest = remaining_nums[1:]
    
    # Try addition
    if can_solve(target, current_val + next_num, rest, enable_concat):
        return True
    
    # Try multiplication
    if can_solve(target, current_val * next_num, rest, enable_concat):
        return True
        
    # Try concatenation
    if enable_concat:
        # Concatenate numbers: 12 || 345 -> 12345
        concat_val = int(str(current_val) + str(next_num))
        if can_solve(target, concat_val, rest, enable_concat):
            return True
        
    return False

def solve(filename):
    equations = parse_input(filename)
    total_part1 = 0
    total_part2 = 0
    
    for target, nums in equations:
        # Check Part 1 (no concat)
        if can_solve(target, nums[0], nums[1:], enable_concat=False):
            total_part1 += target
            total_part2 += target # Valid in P1 is valid in P2
        # Check Part 2 (with concat) if not valid in Part 1
        elif can_solve(target, nums[0], nums[1:], enable_concat=True):
            total_part2 += target
            
    return total_part1, total_part2

def test():
    example_input = [
        "190: 10 19",
        "3267: 81 40 27",
        "83: 17 5",
        "156: 15 6",
        "7290: 6 8 6 15",
        "161011: 16 10 13",
        "192: 17 8 14",
        "21037: 9 7 18 13",
        "292: 11 6 16 20"
    ]
    
    equations = []
    for line in example_input:
        parts = line.split(':')
        target = int(parts[0].strip())
        numbers = list(map(int, parts[1].strip().split()))
        equations.append((target, numbers))
        
    p1 = 0
    p2 = 0
    for target, nums in equations:
        if can_solve(target, nums[0], nums[1:], enable_concat=False):
            p1 += target
            p2 += target
        elif can_solve(target, nums[0], nums[1:], enable_concat=True):
            p2 += target
            
    print(f"Test Part 1: {p1}")
    assert p1 == 3749, f"Expected 3749, got {p1}"
    
    print(f"Test Part 2: {p2}")
    assert p2 == 11387, f"Expected 11387, got {p2}"

if __name__ == "__main__":
    test()
    print("Tests passed!")
    p1, p2 = solve("input-day7.txt")
    print(f"Part 1 Result: {p1}")
    print(f"Part 2 Result: {p2}")
