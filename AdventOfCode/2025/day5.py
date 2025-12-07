def parse_input(filename):
    with open(filename, 'r') as f:
        content = f.read()
    
    parts = content.split('\n\n')
    range_lines = parts[0].strip().split('\n')
    id_lines = parts[1].strip().split('\n')
    
    ranges = []
    for line in range_lines:
        start, end = map(int, line.split('-'))
        ranges.append((start, end))
        
    ids = []
    for line in id_lines:
        ids.append(int(line))
        
    return ranges, ids

def is_fresh(ingredient_id, ranges):
    for start, end in ranges:
        if start <= ingredient_id <= end:
            return True
    return False

def solve_part2(ranges):
    if not ranges:
        return 0
        
    # Sort ranges by start value
    sorted_ranges = sorted(ranges, key=lambda x: x[0])
    
    merged_ranges = []
    current_start, current_end = sorted_ranges[0]
    
    for i in range(1, len(sorted_ranges)):
        next_start, next_end = sorted_ranges[i]
        
        if next_start <= current_end + 1: # Overlapping or adjacent
            current_end = max(current_end, next_end)
        else:
            merged_ranges.append((current_start, current_end))
            current_start, current_end = next_start, next_end
            
    merged_ranges.append((current_start, current_end))
    
    total_fresh = 0
    for start, end in merged_ranges:
        total_fresh += (end - start + 1)
        
    return total_fresh

def main():
    ranges, ids = parse_input('input-day5.txt')
    
    # Part 1
    fresh_count = 0
    for ingredient_id in ids:
        if is_fresh(ingredient_id, ranges):
            fresh_count += 1
            
    print(f"Part 1 - Number of fresh ingredients: {fresh_count}")
    
    # Part 2
    total_fresh_part2 = solve_part2(ranges)
    print(f"Part 2 - Total fresh ingredient IDs: {total_fresh_part2}")

if __name__ == "__main__":
    main()
