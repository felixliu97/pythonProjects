def findCombinations(target, list):
    result[0] = 1
    if 1 in list:
        result[1] = 1
    if 2 in list:
        result[2] = result[0] + result[1]
    for i in range(3, max(list) + 1):
        if i in list:
            result[i] = result[i-1] + result[i-2] + result[i-3]

with open('input-day10.txt', 'r') as f:
    nums = [int(line.strip()) for line in f.readlines()]
    nums.sort()
    prev, def1, def3 = 0, 0, 0
    for num in nums:
        deference = num - prev
        if deference == 1:
            def1 += 1
        if deference == 3:
            def3 += 1
        prev = num
    def3 += 1
    print(f'Result is:', def1 * def3)
    result = [0] * (max(nums) + 1)
    findCombinations(max(nums), nums)
    print(f'Total combinations:', result[-1])