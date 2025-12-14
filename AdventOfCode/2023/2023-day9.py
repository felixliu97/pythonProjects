import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def get_next_val(nums):
    if all(n == 0 for n in nums):
        return 0
    
    diffs = [nums[i+1] - nums[i] for i in range(len(nums)-1)]
    return nums[-1] + get_next_val(diffs)

def get_prev_val(nums):
    if all(n == 0 for n in nums):
        return 0
    
    diffs = [nums[i+1] - nums[i] for i in range(len(nums)-1)]
    return nums[0] - get_prev_val(diffs)

def solve(data):
    lines = data.split('\n')
    sum_next = 0
    sum_prev = 0
    
    for line in lines:
        if not line.strip(): continue
        nums = list(map(int, line.split()))
        sum_next += get_next_val(nums)
        sum_prev += get_prev_val(nums)
        
    return sum_next, sum_prev

def run_tests():
    print("Running tests...")
    example = """0 3 6 9 12 15
1 3 6 10 15 21
10 13 16 21 30 45"""
    
    p1, p2 = solve(example)
    expected_p1 = 114
    expected_p2 = 2
    
    if p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1}")
        
    if p2 == expected_p2:
         print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {p2}")

    print("✅ Tests completed!")

def solve_part1_and_2():
    data = parse_input("2023-day9.txt")
    p1, p2 = solve(data)
    print("--- Part 1 ---")
    print(f"Result: {p1}")
    print("--- Part 2 ---")
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1_and_2()
