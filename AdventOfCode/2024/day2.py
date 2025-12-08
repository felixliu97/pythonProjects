def is_safe(report):
    if len(report) < 2:
        return True
    
    diffs = [report[i+1] - report[i] for i in range(len(report) - 1)]
    
    # Check if all increasing or all decreasing
    is_increasing = all(d > 0 for d in diffs)
    is_decreasing = all(d < 0 for d in diffs)
    
    if not (is_increasing or is_decreasing):
        return False
        
    # Check absolute difference range [1, 3]
    if not all(1 <= abs(d) <= 3 for d in diffs):
        return False
        
    return True

def is_safe_with_dampener(report):
    if is_safe(report):
        return True
        
    for i in range(len(report)):
        new_report = report[:i] + report[i+1:]
        if is_safe(new_report):
            return True
            
    return False

def solve():
    safe_count_p1 = 0
    safe_count_p2 = 0
    try:
        with open('input-day2.txt', 'r') as f:
            for line in f:
                parts = list(map(int, line.strip().split()))
                
                if is_safe(parts):
                    safe_count_p1 += 1
                    
                if is_safe_with_dampener(parts):
                    safe_count_p2 += 1
                    
        print(f"Part 1 Safe reports: {safe_count_p1}")
        print(f"Part 2 Safe reports: {safe_count_p2}")
        
    except FileNotFoundError:
        print("Error: input-day2.txt not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    solve()
