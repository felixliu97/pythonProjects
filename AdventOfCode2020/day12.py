with open('input-day12.txt', 'r') as f:
    movements = [line.strip() for line in f.readlines()]
    east, north, facing = 0, 0, 0
    east2, north2, waypoint_east, waypoint_north = 0, 0, 10, 1

    for move in movements:
        direction = move[0]
        value = int(move[1:])
        if direction in ('E','W'):
            east = east + value if direction == 'E' else east - value
            waypoint_east = waypoint_east + value if direction == 'E' else waypoint_east - value
        elif direction in ('N','S'):
            north = north + value if direction == 'N' else north - value
            waypoint_north = waypoint_north + value if direction == 'N' else waypoint_north - value
        elif direction in ('L','R'):
            facing = ((facing + value) + 360) % 360 if direction == 'R' else ((facing - value) + 360) % 360
            angle = value % 360 if direction == 'R' else 360 - value % 360
            while angle > 0:
                waypoint_east, waypoint_north = waypoint_north, -waypoint_east
                angle -= 90
        elif direction == 'F':
            if facing in (0, 180):
                east = east + value if facing == 0 else east - value
            else:
                north = north + value if facing == 270 else north - value
            east2 += waypoint_east * value
            north2 += waypoint_north * value

    print(f'part1 Manhattan distance is:', abs(east) + abs(north))
    print(f'part2 Manhattan distance is:', abs(east2) + abs(north2))