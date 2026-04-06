import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def run_tests():
    print("Running tests...")
    
    example_input = [
        "MMMSXXMASM",
        "MSAMXMSMSA",
        "AMXSXMAAMM",
        "MSAMASMSMX",
        "XMASAMXAMM",
        "XXAMMXXAMA",
        "SMSMSASXSS",
        "SAXAMASAAA",
        "MAMMMXMMMM",
        "MXMXAXMASX"
    ]
    
    p1_result = count_xmas(example_input)
    expected_p1 = 18
    if p1_result == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1_result}")

    p2_result = count_x_mas(example_input)
    expected_p2 = 9
    if p2_result == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {p2_result}")
        
    print("✅ Tests completed!")

def count_xmas(grid):
    rows = len(grid)
    cols = len(grid[0])
    word = "XMAS"
    word_len = len(word)
    count = 0

    # Directions: (row_delta, col_delta)
    directions = [
        (0, 1),   # Right
        (0, -1),  # Left
        (1, 0),   # Down
        (-1, 0),  # Up
        (1, 1),   # Down-Right
        (1, -1),  # Down-Left
        (-1, 1),  # Up-Right
        (-1, -1)  # Up-Left
    ]

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != 'X':
                continue
            
            for dr, dc in directions:
                if 0 <= r + dr * (word_len - 1) < rows and \
                   0 <= c + dc * (word_len - 1) < cols:
                    match = True
                    for i in range(word_len):
                        if grid[r + dr * i][c + dc * i] != word[i]:
                            match = False
                            break
                    if match:
                        count += 1
    return count

def count_x_mas(grid):
    rows = len(grid)
    cols = len(grid[0])
    count = 0
    
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if grid[r][c] == 'A':
                tl = grid[r-1][c-1]
                br = grid[r+1][c+1]
                d1_valid = (tl == 'M' and br == 'S') or (tl == 'S' and br == 'M')
                
                tr = grid[r-1][c+1]
                bl = grid[r+1][c-1]
                d2_valid = (tr == 'M' and bl == 'S') or (tr == 'S' and bl == 'M')
                
                if d1_valid and d2_valid:
                    count += 1
    return count

def solve_part1():
    print("--- Part 1 ---")
    grid = parse_input("2024-day4.txt")
    result = count_xmas(grid)
    print(f"Result: {result}")

def solve_part2():
    print("--- Part 2 ---")
    grid = parse_input("2024-day4.txt")
    result = count_x_mas(grid)
    print(f"Result: {result}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
