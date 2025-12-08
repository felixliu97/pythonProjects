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
            # Optimization: only check starting from 'X'
            if grid[r][c] != 'X':
                continue
            
            for dr, dc in directions:
                # Check if the word fits in this direction
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
    
    # We need the 'A' to be at least one step away from the borders
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if grid[r][c] == 'A':
                # Check diagonals
                # Diagonal 1: Top-Left to Bottom-Right
                tl = grid[r-1][c-1]
                br = grid[r+1][c+1]
                d1_valid = (tl == 'M' and br == 'S') or (tl == 'S' and br == 'M')
                
                # Diagonal 2: Top-Right to Bottom-Left
                tr = grid[r-1][c+1]
                bl = grid[r+1][c-1]
                d2_valid = (tr == 'M' and bl == 'S') or (tr == 'S' and bl == 'M')
                
                if d1_valid and d2_valid:
                    count += 1
    return count

def solve(filename):
    try:
        with open(filename, 'r') as f:
            grid = [line.strip() for line in f.readlines()]
        part1 = count_xmas(grid)
        part2 = count_x_mas(grid)
        return part1, part2
    except FileNotFoundError:
        print(f"Error: File {filename} not found.")
        return 0, 0

def test():
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
    print(f"Part 1 Test Result: {p1_result}")
    assert p1_result == 18, f"Expected 18, got {p1_result}"

    p2_result = count_x_mas(example_input)
    print(f"Part 2 Test Result: {p2_result}")
    assert p2_result == 9, f"Expected 9, got {p2_result}"

if __name__ == "__main__":
    test()
    print("Tests passed!")
    p1, p2 = solve("input-day4.txt")
    print(f"Part 1 Result: {p1}")
    print(f"Part 2 Result: {p2}")
