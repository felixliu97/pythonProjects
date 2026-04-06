def findSmallestNumber(x, mod_x, y, mod_y):
    mod_x = mod_x % x
    mod_y = mod_y % y
    smaller = x if x < y else y
    larger = y if x < y else x
    diff = abs(y-x) 
    mod_diff = (mod_y - mod_x + smaller) % smaller if x < y else (mod_x - mod_y + smaller) % smaller
    for i in range(1, smaller):
        num = i * diff + mod_diff
        if num % smaller == 0:
            break
    return (lcm(x, y), i * larger + (mod_y if y > x else mod_x))

def gcd(x, y):
    while y:
        x, y = y, x%y
    return x

def lcm(x, y):
    return int(x * y / gcd(x, y))

with open('input-day13.txt', 'r') as f:
    timestamp = int(f.readline().strip())
    timetable = f.readline().strip().split(',')
    buses = [int(n) for n in timetable if n != 'x']
    min_bus, min_wait = 0, 1000
    for bus in buses:
        wait = bus - timestamp % bus
        if wait < min_wait:
            min_wait = wait
            min_bus = bus
    print(f'part1 result:', min_bus * min_wait)

    relevant_buses = [(int(bus), int(minute)) for minute, bus in enumerate(timetable) if bus != 'x']
    x = relevant_buses[0][0]
    mod_x = (x - relevant_buses[0][1] % x) % x
    for num, mod in relevant_buses[1:]:
        y = num
        mod_y = (y - mod % y) % y
        x, mod_x = findSmallestNumber(x, mod_x, y, mod_y)
    print(f'part2 result:', mod_x)