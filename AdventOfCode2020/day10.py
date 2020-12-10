def findCombinations(target, list):
    result[0] = 1
    if 1 in list:
        result[1] = 1
    if 2 in list:
        result[2] = result[0] + result[1]
    for i in range(3, max(list) + 1):
        if i in list:
            result[i] = result[i-1] + result[i-2] + result[i-3]
    return result[target]

with open('input-day10.txt', 'r') as f:
    nums = sorted([int(line.strip()) for line in f.readlines()])
    prev, dif1, dif3 = 0, 0, 0
    for num in nums:
        difference = num - prev
        if difference == 1:
            dif1 += 1
        if difference == 3:
            dif3 += 1
        prev = num
    dif3 += 1
    print(f'Result is:', dif1 * dif3)
    result = [0] * (max(nums) + 1)
    print(f'Total combinations:', findCombinations(max(nums), nums))