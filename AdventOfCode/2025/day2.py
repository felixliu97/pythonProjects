def is_invalid_part1(n):
    s = str(n)
    if len(s) % 2 != 0:
        return False
    mid = len(s) // 2
    return s[:mid] == s[mid:]

def is_invalid_part2(n):
    s = str(n)
    # Check if s is formed by repeating a substring at least twice.
    # This is true if and only if s is found in (s + s)[1:-1].
    return s in (s + s)[1:-1]

def solve():
    try:
        with open('input-day2.txt', 'r') as f:
            content = f.read().strip()
    except FileNotFoundError:
        print("Error: input-day2.txt not found.")
        return

    ranges = content.split(',')
    total_invalid_sum_part1 = 0
    total_invalid_sum_part2 = 0
    
    for r in ranges:
        if not r: continue
        try:
            start_str, end_str = r.split('-')
            start = int(start_str)
            end = int(end_str)
            
            for num in range(start, end + 1):
                if is_invalid_part1(num):
                    total_invalid_sum_part1 += num
                if is_invalid_part2(num):
                    total_invalid_sum_part2 += num
        except ValueError:
            print(f"Skipping invalid range format: {r}")
            continue

    print(f"Part 1 - Total sum of invalid IDs: {total_invalid_sum_part1}")
    print(f"Part 2 - Total sum of invalid IDs: {total_invalid_sum_part2}")

if __name__ == '__main__':
    solve()
