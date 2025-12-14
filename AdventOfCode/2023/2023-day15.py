import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            # Input is one long line, comma separated. Ignore newlines.
            return f.read().replace('\n', '').strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def hash_algo(s):
    current_val = 0
    for char in s:
        current_val += ord(char)
        current_val *= 17
        current_val %= 256
    return current_val

def solve_part1(data):
    steps = data.split(',')
    total = 0
    for step in steps:
        total += hash_algo(step)
    return total

def solve_part2(data):
    steps = data.split(',')
    boxes = [[] for _ in range(256)]
    # box structure: list of [label, focal_length]
    
    for step in steps:
        if '-' in step:
            label = step[:-1]
            box_idx = hash_algo(label)
            # Remove
            # Create new list without the label
            # or modify in place
            boxes[box_idx] = [lens for lens in boxes[box_idx] if lens[0] != label]
        elif '=' in step:
            label, fl_str = step.split('=')
            focal_length = int(fl_str)
            box_idx = hash_algo(label)
            
            # Check if exists
            found = False
            for lens in boxes[box_idx]:
                if lens[0] == label:
                    lens[1] = focal_length
                    found = True
                    break
            if not found:
                boxes[box_idx].append([label, focal_length])
                
    # Calculate power
    total_power = 0
    for i, box in enumerate(boxes):
        for slot, lens in enumerate(box):
            power = (1 + i) * (1 + slot) * lens[1]
            total_power += power
            
    return total_power

def solve(data):
    p1 = solve_part1(data)
    p2 = solve_part2(data)
    return p1, p2

def run_tests():
    print("Running tests...")
    example = "rn=1,cm-,qp=3,cm=2,qp-,pc=4,ot=9,ab=5,pc-,pc=6,ot=7"
    
    p1 = solve_part1(example)
    expected_p1 = 1320
    
    if p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1}")
        
    p2 = solve_part2(example)
    expected_p2 = 145 
    # Explanation from common knowledge of this problem / deductive:
    # rn=1 -> Box 0: [rn 1]
    # cm- -> Box 0: [rn 1] (cm hashes to 0? h(rn)=30, h(cm)=253. No.)
    # Let's trace carefully or just run it.
    # rn: 30. cm: 253. qp: 97. pc: 3. ot: 9. ab: 197.
    # Box 0: [rn 1] -> [rn 1, cm 2] -> [rn 1] (cm removed) -> ...
    # Wait, example says:
    # rn=1: Box 0.
    # cm-: Box 0 (if cm hashes to 0).
    # qp=3: Box 1.
    # ...
    # Example Part 2 Power sum is 145.
    
    if p2 == expected_p2:
         print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {p2}")

    print("✅ Tests completed!")

def solve_part1_and_2():
    # print("Reading input...", flush=True) 
    # Standard format: clean output
    data = parse_input("2023-day15.txt")
    p1, p2 = solve(data)
    print("--- Part 1 ---")
    print(f"Result: {p1}")
    print("--- Part 2 ---")
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1_and_2()
