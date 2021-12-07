increased = 0
depth = None

with open('input-day1.txt', 'r') as f:
    nums = [int(line.replace('\n','')) for line in f.readlines()]
    for num in nums:
        if depth is None:
            depth = num
        else:
            if num > depth:
                increased += 1
            depth = num

print(f"increased: {increased}")

window = 3
window_depth_sum = [sum(nums[i:i+window]) for i in range(len(nums) - window + 1)]
window_depth = None
increased = 0

for sum in window_depth_sum:
    if window_depth is None:
        window_depth = sum
    else:
        if sum > window_depth:
            increased += 1
        window_depth = sum

print(f"window increased: {increased}")
