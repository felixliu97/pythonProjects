neighbors_3d = [(x, y, z) for x in range(-1, 2) for y in range(-1, 2) for z in range(-1, 2) if not (x == 0 and y == 0 and z == 0)]
neighbors_4d = [(x, y, z, w) for x in range(-1, 2) for y in range(-1, 2) for z in range(-1, 2) for w in range(-1, 2) if not (x == 0 and y == 0 and z == 0 and w == 0)]

def count_active(coordinate, active_list):
    if len(coordinate) == 3:
        x, y, z = coordinate 
        neighbors_list = [(x + dx, y + dy, z + dz) for dx, dy, dz in neighbors_3d]
    else:
        x, y, z, w = coordinate 
        neighbors_list = [(x + dx, y + dy, z + dz, w + dw) for dx, dy, dz, dw in neighbors_4d]
    return (len(set(active_list).intersection(neighbors_list)))

def iterate(active_list, dimensions):
    copy = active_list[:]
    if dimensions == 3:
        min_x, max_x = min([x for x, y, z in active_list]), max([x for x, y, z in active_list])
        min_y, max_y = min([y for x, y, z in active_list]), max([y for x, y, z in active_list])
        min_z, max_z = min([z for x, y, z in active_list]), max([z for x, y, z in active_list])
        for x, y, z in active_list:
            if count_active((x, y, z), active_list) not in (2, 3):
                copy.remove((x, y, z))
        for x in range(min_x - 1, max_x + 2):
            for y in range(min_y - 1, max_y + 2):
                for z in range(min_z - 1, max_z + 2):
                    if (x, y, z) not in active_list and count_active((x, y, z), active_list) == 3:
                        copy.append((x, y, z))
    else:
        min_x, max_x = min([x for x, y, z, w in active_list]), max([x for x, y, z, w in active_list])
        min_y, max_y = min([y for x, y, z, w in active_list]), max([y for x, y, z, w in active_list])
        min_z, max_z = min([z for x, y, z, w in active_list]), max([z for x, y, z, w in active_list])
        min_w, max_w = min([w for x, y, z, w in active_list]), max([w for x, y, z, w in active_list])
        for x, y, z, w in active_list:
            if count_active((x, y, z, w), active_list) not in (2, 3):
                copy.remove((x, y, z, w))
        for x in range(min_x - 1, max_x + 2):
            for y in range(min_y - 1, max_y + 2):
                for z in range(min_z - 1, max_z + 2):
                    for w in range(min_w - 1, max_w + 2):
                        if (x, y, z, w) not in active_list and count_active((x, y, z, w), active_list) == 3:
                            copy.append((x, y, z, w))
    return copy

with open('input-day17.txt', 'r') as f:
    cube = [line.strip() for line in f.readlines()]
    z, w = 0, 0
    active_3d = []
    active_4d = []
    for x, row in enumerate(cube):
        for y, value in enumerate(row):
            if value == '#':
                active_3d.append((x, y, z))
                active_4d.append((x, y, z, w))

    for _ in range(6):
        active_3d = iterate(active_3d, 3)
        active_4d = iterate(active_4d, 4)

print(f'3d active count:', len(active_3d))
print(f'4d active count:', len(active_4d))