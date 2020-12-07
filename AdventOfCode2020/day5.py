import re
seats = []

with open('input-day5.txt', 'r') as f:
    for line in f.readlines():
        line = line.strip()
        if re.match(r'^(B|F){7}(L|R){3}$', line):
            line = line.replace("F","0").replace("B","1").replace("L","0").replace("R","1")
            seats.append(line)

    seats_10_base = sorted([int(x[:7],2) * 8 + int(x[-3:],2) for x in seats])
    firstseat, lastseat = seats_10_base[0], seats_10_base[-1]
    print(lastseat)

    left, right, missing = 0, lastseat - firstseat, -1
    # binary search
    while (left <= right):
        mid = (left + right) // 2
        if seats_10_base[mid] != mid + firstseat and seats_10_base[mid-1] == mid - 1 + firstseat:
            missing = mid
            break
        if seats_10_base[mid] == mid + firstseat:
            left = mid + 1
        else:
            right = mid - 1
 
    print(missing + firstseat)