with open('input-day10.txt', 'r') as f:
    nums = [int(line.strip()) for line in f.readlines()]
    nums.sort()
    prev, def1, def3 = 0, 0, 0
    essentials = [0]
    for num in nums:
        deference = num - prev
        if deference == 1:
            def1 += 1
        if deference == 3:
            def3 += 1
            if num-3 not in essentials:
                essentials.append(num-3)
            essentials.append(num)
        prev = num
    def3 += 1
    essentials.append(num)
    print(f'Result is:', def1 * def3)
    # print(essentials)

    optionals = list(set(nums) - set(essentials))
    optionals.sort()
    # print(optionals)
    combinations = 1

    for i in range(0, len(essentials) - 1):
        start = essentials[i]
        end = essentials[i+1]
        # print(start, end)
        if (start + 2 == end or start + 3 == end):
            for n in optionals:
                if start < n < end:
                    combinations *= 2
                if n > end:
                    break
        else:
            window = [x for x in optionals if start < x < end]
            # print(window)
            if len(window) > 1:
                window_combination = pow(2,len(window)) - 1
                combinations *= window_combination
    print(f'Overall combinations:', combinations)