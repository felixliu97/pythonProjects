def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            line = f.read().strip()
        return line
    except FileNotFoundError:
        print(f"Error: File {filename} not found.")
        return ""

def solve_part1(filename):
    disk_map = parse_input(filename)
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

def solve_part2(filename):
    disk_map = parse_input(filename)
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
            # If space is perfectly used, remove it? simpler to just set its len to 0 or update
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

def test():
    example_input = "2333133121414131402"
    
    # Part 1 logic test
    blocks = []
    file_id = 0
    for i, char in enumerate(example_input):
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
    
    c1 = 0
    for i, fid in enumerate(blocks):
        if fid != -1: c1 += i * fid
    print(f"Test Part 1: {c1}")
    assert c1 == 1928, f"Expected 1928, got {c1}"

    # Part 2 logic test
    files = {}
    free_spaces = []
    current_pos = 0
    file_id = 0
    
    for i, char in enumerate(example_input):
        length = int(char)
        if i % 2 == 0:
            files[file_id] = {'start': current_pos, 'len': length}
            file_id += 1
        else:
            if length > 0: free_spaces.append({'start': current_pos, 'len': length})
        current_pos += length
        
    for fid in range(file_id - 1, -1, -1):
        file_info = files[fid]
        file_len = file_info['len']
        file_start = file_info['start']
        
        best_space_idx = -1
        for i, space in enumerate(free_spaces):
            if space['start'] >= file_start: break
            if space['len'] >= file_len:
                best_space_idx = i
                break
        
        if best_space_idx != -1:
            space = free_spaces[best_space_idx]
            files[fid]['start'] = space['start']
            if space['len'] == file_len:
                free_spaces.pop(best_space_idx)
            else:
                free_spaces[best_space_idx]['start'] += file_len
                free_spaces[best_space_idx]['len'] -= file_len

    c2 = 0
    for fid, info in files.items():
        start = info['start']
        length = info['len']
        for i in range(length):
            c2 += fid * (start + i)
            
    print(f"Test Part 2: {c2}")
    assert c2 == 2858, f"Expected 2858, got {c2}"

if __name__ == "__main__":
    test()
    print("Tests passed!")
    p1 = solve_part1("input-day9.txt")
    print(f"Part 1 Result: {p1}")
    p2 = solve_part2("input-day9.txt")
    print(f"Part 2 Result: {p2}")
