with open("input-day4.txt") as f:
    lines = f.read().strip().split("\n")

sum = 0
for _, line in enumerate(lines):
    _, game = line.split(':')
    numbers = game.split('|')
    winning_nums = [int(n) for n in numbers[0].split()]
    my_nums = [int(n) for n in numbers[1].split()]
    my_winning_nums = set(winning_nums) & set(my_nums)

    if my_winning_nums:
       sum += 2 ** (len(my_winning_nums) - 1)
    
print(sum)