def parse_schematic(schematic_str):
    rows = schematic_str.strip().split('\n')
    heights = []
    # Grid is 7 rows, 5 cols
    for col in range(5):
        count = 0
        for row in range(7):
            if rows[row][col] == '#':
                count += 1
        heights.append(count - 1)
    
    is_lock = (rows[0] == '#####')
    return is_lock, heights

def parse_input(filename):
    locks = []
    keys = []
    
    try:
        with open(filename, 'r') as f:
            content = f.read().strip()
    except FileNotFoundError:
        return None, None
        
    schematics = content.split('\n\n')
    
    for s in schematics:
        if not s.strip():
            continue
        is_lock, heights = parse_schematic(s)
        if is_lock:
            locks.append(heights)
        else:
            keys.append(heights)
            
    return locks, keys

def parse_example(example_str):
    locks = []
    keys = []
    schematics = example_str.strip().split('\n\n')
    for s in schematics:
        if not s.strip():
            continue
        is_lock, heights = parse_schematic(s)
        if is_lock:
            locks.append(heights)
        else:
            keys.append(heights)
    return locks, keys

def check_fit(lock, key):
    # Total available space is 5 unique rows between top and bottom rails.
    # Lock height + Key height <= 5 in every column.
    for i in range(5):
        if lock[i] + key[i] > 5:
            return False
    return True

def solve():
    # Example
    example_input = """#####
.####
.####
.####
.#.#.
.#...
.....

#####
##.##
.#.##
...##
...#.
...#.
.....

.....
#....
#....
#...#
#.#.#
#.###
#####

.....
.....
#.#..
###..
###.#
###.#
#####

.....
.....
.....
#....
#.#..
#.#.#
#####"""
    
    locks_ex, keys_ex = parse_example(example_input)
    fits_ex = 0
    for lock in locks_ex:
        for key in keys_ex:
            if check_fit(lock, key):
                fits_ex += 1
                
    print(f"Example Fits: {fits_ex} (Expected 3)")
    assert fits_ex == 3
    print("Example passed!")

    # Real Input
    locks, keys = parse_input('input-day25.txt')
    if locks is not None:
        valid_pairs = 0
        for lock in locks:
            for key in keys:
                if check_fit(lock, key):
                    valid_pairs += 1
                    
        print(f"\nPart 1 Final Result: {valid_pairs}")
    else:
        print("input-day25.txt not found.")

if __name__ == '__main__':
    solve()
