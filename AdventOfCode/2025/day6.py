import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            lines = f.read().splitlines()
        return lines
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def get_blocks(lines):
    if not lines:
        return []

    max_len = max(len(line) for line in lines)
    # Right padding spaces to ensure even columns
    padded_lines = [line.ljust(max_len) for line in lines]
    
    # Identify empty columns (columns consisting entirely of spaces)
    empty_cols = []
    for col_idx in range(max_len):
        is_empty = True
        for row_idx in range(len(padded_lines)):
            if padded_lines[row_idx][col_idx] != ' ':
                is_empty = False
                break
        if is_empty:
            empty_cols.append(col_idx)
            
    blocks = []
    start_col = 0
    # Add a sentinel to handle the last block
    split_points = empty_cols + [max_len]
    
    for split_col in split_points:
        if split_col > start_col:
            block = []
            for line in padded_lines:
                # Extract the slice for this block
                block.append(line[start_col:split_col])
            blocks.append(block)
        start_col = split_col + 1
        
    return blocks

def solve_block_part1(block):
    # Rows logic: Numbers are vertical lines above the operator
    # Remove empty lines from the block view (though in this puzzle format, 
    # rows are usually consistent across the width, but per-block we care about non-empty)
    
    # Clean up right/left whitespace on rows for Part 1 parsing
    rows = [row.strip() for row in block]
    rows = [r for r in rows if r] # filter empty strings
    
    if not rows: return 0
    
    # The operator is at the bottom
    operator_char = rows[-1]
    
    # The numbers are above
    number_rows = rows[:-1]
    numbers = []
    for r in number_rows:
        try:
            numbers.append(int(r))
        except ValueError:
            pass
            
    if not numbers:
        return 0
        
    result = numbers[0]
    for num in numbers[1:]:
        if operator_char == '+':
            result += num
        elif operator_char == '*':
            result *= num
            
    return result

def solve_block_part2(block):
    # Column logic: Right-to-Left columns.
    # Rows in the block are strictly aligned.
    
    # Filter out empty rows first to find operator and grid
    # But wait, we need the original alignment for columns.
    # So we just find the last non-empty row index for the operator.
    
    non_empty_indices = [i for i, r in enumerate(block) if r.strip()]
    if not non_empty_indices:
        return 0
        
    last_idx = non_empty_indices[-1]
    operator_char = block[last_idx].strip()
    
    # The numbers are in rows up to last_idx (exclusive)
    grid_rows = block[:last_idx]
    if not grid_rows:
        return 0
        
    width = len(grid_rows[0])
    numbers = []
    
    # Iterate columns Right-to-Left
    for col in range(width - 1, -1, -1):
        digits = []
        for r in grid_rows:
            if col < len(r) and r[col] != ' ':
                digits.append(r[col])
        
        if digits:
            try:
                val = int("".join(digits))
                numbers.append(val)
            except ValueError:
                pass
                
    if not numbers:
        return 0
        
    result = numbers[0]
    for num in numbers[1:]:
        if operator_char == '+':
            result += num
        elif operator_char == '*':
            result *= num
            
    return result

def run_tests():
    print("Running tests...")
    
    example_input = """
123 328  51 64 
 45 64  387 23 
  6 98  215 314
*   +   *   +  
"""
    # Remove initial newline for cleaner splitting but keep indentation structure 
    # actually leading/trailing whitespace matter for the first/last lines?
    # The example string has a leading newline. splitlines() handles it.
    
    lines = example_input.strip('\n').splitlines()
    blocks = get_blocks(lines)
    
    print(f"Debug: Found {len(blocks)} blocks.")
    
    # Part 1 Verification
    p1_total = sum(solve_block_part1(b) for b in blocks)
    expected_p1 = 4277556
    
    print(f"Example Part 1 Sum: {p1_total}")
    if p1_total == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1_total}")
        
    # Part 2 Verification
    # Expected: 1058 + 3253600 + 625 + 8544 = 3263827
    p2_total = sum(solve_block_part2(b) for b in blocks)
    expected_p2 = 3263827
    
    print(f"Example Part 2 Sum: {p2_total}")
    if p2_total == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {p2_total}")

    print("✅ Tests completed!")

def solve_part1():
    print("--- Part 1 ---")
    lines = parse_input('input-day6.txt')
    blocks = get_blocks(lines)
    total = sum(solve_block_part1(b) for b in blocks)
    print(f"Result: {total}")

def solve_part2():
    print("--- Part 2 ---")
    lines = parse_input('input-day6.txt')
    blocks = get_blocks(lines)
    total = sum(solve_block_part2(b) for b in blocks)
    print(f"Result: {total}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
