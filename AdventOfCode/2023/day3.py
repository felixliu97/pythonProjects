import itertools
import math
import re

with open("input-day3.txt") as f:
    ls = f.read().strip().split("\n")

box = list(itertools.product((-1, 0, 1), (-1, 0, 1)))
parts_by_symbol = {
    (i, j): (x, [])
    for i, l in enumerate(ls)
    for j, x in enumerate(l)
    if x != "." and not x.isdigit()
}
# print(parts_by_symbol)

part_sum = 0

for i, l in enumerate(ls):
    for match in re.finditer(r"\d+", l):
        n = int(match.group(0))
        boundary = {
            (i + di, j + dj)
            for di, dj in box
            for j in range(match.start(), match.end())
        }
        # print(boundary)
        if parts_by_symbol.keys() & boundary:
            part_sum += n
        for symbol in parts_by_symbol.keys() & boundary:
            parts_by_symbol[symbol][1].append(n)

# print(parts_by_symbol)

# Part 1
print(part_sum)

# Part 2
print(
    sum(
        math.prod(parts)
        for symbol, parts in parts_by_symbol.values()
        if len(parts) == 2 and symbol == "*"
    )
)
