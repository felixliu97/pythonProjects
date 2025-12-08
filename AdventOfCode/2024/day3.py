import re

def solve_part1(data):
    # Regex to find valid mul(X,Y) instructions
    # X and Y are 1-3 digit numbers
    pattern = r"mul\((\d{1,3}),(\d{1,3})\)"
    matches = re.findall(pattern, data)
    
    total_sum = 0
    for x, y in matches:
        total_sum += int(x) * int(y)
        
    return total_sum

def solve_part2(data):
    # Regex to find mul(X,Y), do(), and don't()
    # Captures:
    # 1. mul(X,Y) -> groups 1 & 2 are numbers
    # 2. do() -> group 3 is non-None (if we group it explicitly) logic is simpler with flat matching
    # Let's use a combined pattern and check the match text or groups
    
    # Pattern explanation:
    # mul\((\d{1,3}),(\d{1,3})\)  Matches mul instructions
    # do\(\)                      Matches do()
    # don't\(\)                   Matches don't()
    pattern = r"mul\((\d{1,3}),(\d{1,3})\)|do\(\)|don't\(\)"
    
    matches = re.finditer(pattern, data)
    
    total_sum = 0
    enabled = True # Enabled at start
    
    for match in matches:
        text = match.group(0)
        if text == "do()":
            enabled = True
        elif text == "don't()":
            enabled = False
        elif text.startswith("mul"):
            if enabled:
                x, y = match.group(1), match.group(2)
                total_sum += int(x) * int(y)
                
    return total_sum

def main():
    # Part 1 Example
    example_data_p1 = "xmul(2,4)%&mul[3,7]!@^do_not_mul(5,5)+mul(32,64]then(mul(11,8)mul(8,5))"
    example_result_p1 = solve_part1(example_data_p1)
    print(f"Part 1 Example result: {example_result_p1}")
    assert example_result_p1 == 161, f"Expected 161, got {example_result_p1}"

    # Part 2 Example
    example_data_p2 = "xmul(2,4)&mul[3,7]!^don't()_mul(5,5)+mul(32,64](mul(11,8)undo()?mul(8,5))"
    example_result_p2 = solve_part2(example_data_p2)
    print(f"Part 2 Example result: {example_result_p2}")
    assert example_result_p2 == 48, f"Expected 48, got {example_result_p2}"

    try:
        with open("input-day3.txt", "r") as f:
            data = f.read()
        
        result_p1 = solve_part1(data)
        print(f"Part 1 result: {result_p1}")

        result_p2 = solve_part2(data)
        print(f"Part 2 result: {result_p2}")
        
    except FileNotFoundError:
        print("input-day3.txt not found. Please ensure the file exists.")

if __name__ == "__main__":
    main()
