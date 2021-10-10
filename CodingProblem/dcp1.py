from operator import mul
from functools import reduce

with open('input/dcp1.txt', 'r') as f:
    nums = [int(n) for n in f.readline().strip().split(',')]
    print(f"Input: {nums}")

    output = []

    for num in nums:
        copy = nums[:]
        copy.remove(num)
        output.append(reduce(mul, copy, 1))

    print(f"Output: {output}")