def part1():
    new_list = []
    for num in list:
        counterpart = targetSum - num
        if counterpart in new_list:
            print(num, counterpart)
            print(num * counterpart)
            return
        new_list.append(num)
    print("No result found - Two Sum")

def part2():
    length = len(list)
    for i in range(0, length - 2):
        j, k = i + 1, length - 1
        while j < k:
            three_sum = list[i] + list[j] + list[k]
            if three_sum == targetSum:
                print(list[i], list[j], list[k])
                print(list[i] * list[j] * list[k])
                return
            elif three_sum < targetSum:
                j += 1
            else:
                k -= 1
    print("No result found - Three Sum")

list = []
targetSum = 2020
file = open('input-day1.txt', 'r') 
lines = file.readlines()
for line in lines:
    line = int(line.strip())
    list.append(line)
list.sort()

part1()
part2()