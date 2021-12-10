x, y = 0, 0
ax, ay, aim = 0, 0, 0

with open('input-day2.txt', 'r') as f:
    operations = [line.replace('\n','') for line in f.readlines()]
    for operation in operations:
        direction, distance_t = operation.split()
        distance = int(distance_t)
        match direction:
            case 'forward':
                x += distance
                ax += distance
                ay += distance * aim
            case 'up':
                y -= distance
                aim -= distance
            case 'down':
                y += distance
                aim += distance

print(f"x: {x}, y:{y}, x*y: {x*y}")
print(f"aim: {aim}, ax: {ax}, ay:{ay}, ax*ay: {ax*ay}")