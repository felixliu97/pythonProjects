def parse_input(filename):
    with open(filename, 'r') as f:
        lines = f.read().splitlines()
    
    if not lines:
        return []

    max_len = max(len(line) for line in lines)
    padded_lines = [line.ljust(max_len) for line in lines]
    
    # Identify empty columns
    empty_cols = []
    for col_idx in range(max_len):
        is_empty = True
        for row_idx in range(len(padded_lines)):
            if padded_lines[row_idx][col_idx] != ' ':
                is_empty = False
                break
        if is_empty:
            empty_cols.append(col_idx)
            
    # Group columns into blocks
    blocks = []
    start_col = 0
    # Add a sentinel empty column at the end if needed, or just handle the last block
    split_points = empty_cols + [max_len]
    
    for split_col in split_points:
        if split_col > start_col:
            # Extract block
            block = []
            for line in padded_lines:
                block.append(line[start_col:split_col])
            blocks.append(block)
        start_col = split_col + 1
        
    return blocks

def solve_problem(block):
    # Operator is in the last row, usually centered or somewhere in the row
    # Numbers are in the rows above
    
    # Filter out empty rows if any (though input desc says operator is at bottom)
    # The last non-empty row should contain the operator
    
    rows = [row for row in block if row.strip()]
    if not rows:
        return 0
        
    operator_row = rows[-1]
    operator_char = operator_row.strip()
    
    # Numbers are in the remaining rows
    number_rows = rows[:-1]
    numbers = []
    
    for row in number_rows:
        stripped = row.strip()
        if stripped:
            try:
                numbers.append(int(stripped))
            except ValueError:
                pass # Should not happen based on description
                
    if not numbers:
        return 0
        
    result = numbers[0]
    for num in numbers[1:]:
        if operator_char == '+':
            result += num
        elif operator_char == '*':
            result *= num
        else:
            # Fallback or unknown operator
            pass
            
    return result

def solve_problem_part2(block):
    rows = [row for row in block if row.strip()]
    if not rows:
        return 0
        
    operator_row = rows[-1]
    operator_char = operator_row.strip()
    
    # Numbers are in the columns of the remaining rows
    number_rows = rows[:-1]
    if not number_rows:
        return 0
        
    width = len(number_rows[0])
    numbers = []
    
    for col_idx in range(width):
        col_str = ""
        for row in number_rows:
            if col_idx < len(row):
                col_str += row[col_idx]
        
        stripped = col_str.strip()
        if stripped:
            try:
                numbers.append(int(stripped))
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
        else:
            pass
            
    return result

def main():
    blocks = parse_input('input-day6.txt')
    
    # Part 1
    grand_total = 0
    for block in blocks:
        grand_total += solve_problem(block)
        
    print(f"Part 1 - Grand total: {grand_total}")
    
    # Part 2
    grand_total_part2 = 0
    for block in blocks:
        grand_total_part2 += solve_problem_part2(block)
        
    print(f"Part 2 - Grand total: {grand_total_part2}")

if __name__ == "__main__":
    main()
