import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            line = f.read().strip()
        return line
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def run_tests():
    print("Running tests...")
    
    example_input = "2333133121414131402"
    
    # Part 1 logic test
    p1 = solve_logic_part1(example_input)
    print(f"Test Part 1: {p1}")
    expected_p1 = 1928
    if p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1}")

    # Part 2 logic test
    p2 = solve_logic_part2(example_input)
    print(f"Test Part 2: {p2}")
    expected_p2 = 2858
    if p2 == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {p2}")
        
    print("✅ Tests completed!")

def solve_logic_part1(disk_map):
    if not disk_map:
        return 0
        
    blocks = []
    file_id = 0
    for i, char in enumerate(disk_map):
        length = int(char)
        if i % 2 == 0:
            blocks.extend([file_id] * length)
            file_id += 1
        else:
            blocks.extend([-1] * length)
            
    left = 0
    right = len(blocks) - 1
    
    while left < right:
        while left < len(blocks) and blocks[left] != -1: left += 1
        while right >= 0 and blocks[right] == -1: right -= 1
        if left >= right: break
        
        blocks[left] = blocks[right]
        blocks[right] = -1
        
    checksum = 0
    for i, file_id in enumerate(blocks):
        if file_id != -1:
            checksum += i * file_id
            
    return checksum

def solve_logic_part2(disk_map):
    if not disk_map: return 0
    
    files = {} # id -> {start, len}
    free_spaces = [] # list of {start, len}
    
    current_pos = 0
    file_id = 0
    
    for i, char in enumerate(disk_map):
        length = int(char)
        if i % 2 == 0:
            files[file_id] = {'start': current_pos, 'len': length}
            file_id += 1
        else:
            if length > 0:
                free_spaces.append({'start': current_pos, 'len': length})
        current_pos += length
        
    max_id = file_id - 1
    
    # Try to move each file from max_id down to 0
    for fid in range(max_id, -1, -1):
        file_info = files[fid]
        file_len = file_info['len']
        file_start = file_info['start']
        
        # Find leftmost suitable free space
        best_space_idx = -1
        for i, space in enumerate(free_spaces):
            if space['start'] >= file_start:
                break # Space is to the right of file, cannot move
            
            if space['len'] >= file_len:
                best_space_idx = i
                break
        
        if best_space_idx != -1:
            space = free_spaces[best_space_idx]
            
            # Move file
            files[fid]['start'] = space['start']
            
            # Update space
            remaining_len = space['len'] - file_len
            if remaining_len == 0:
                free_spaces.pop(best_space_idx)
            else:
                free_spaces[best_space_idx]['start'] += file_len
                free_spaces[best_space_idx]['len'] -= file_len
                
    # Calculate checksum
    checksum = 0
    for fid, info in files.items():
        start = info['start']
        length = info['len']
        for i in range(length):
            checksum += fid * (start + i)
            
    return checksum


def solve_part1():
    print("--- Part 1 ---")
    data = parse_input("input-day9.txt")
    result = solve_logic_part1(data)
    print(f"Result: {result}")

def solve_part2():
    print("--- Part 2 ---")
    data = parse_input("input-day9.txt")
    result = solve_logic_part2(data)
    print(f"Result: {result}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
