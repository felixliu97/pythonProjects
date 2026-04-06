import re

file = open('input-day2.txt', 'r') 
lines = file.readlines()
valid_part1, valid_part2 = 0, 0
for line in lines:
    res = re.match(r'^([0-9]+)-([0-9]+) ([a-z]): ([a-z]+)$', line)
    lower = int(res.group(1))
    upper = int(res.group(2))
    letter = res.group(3)
    password = res.group(4)
    if lower <= (password.count(letter)) <= upper:
        valid_part1 += 1
    if [password[lower-1], password[upper-1]].count(letter) == 1:
        valid_part2 += 1

print(valid_part1)
print(valid_part2)