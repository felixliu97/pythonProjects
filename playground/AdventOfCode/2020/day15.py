def findNthNumber(numbers, n):
    copy = numbers[:]
    dict = {}
    if copy[-1] not in copy[:-1]:
        numbers.append(0)

    for i in range(1, n+1):
        next_num = copy.pop(0)
        if next_num in dict:
            copy.append(i - dict[next_num])
        elif not copy:
            copy.append(0)
        dict[next_num] = i
    return next_num

numbers = [8,0,17,4,1,12]

print(f'part 1:',findNthNumber(numbers, 2020))
print(f'part 2:',findNthNumber(numbers, 30000000))