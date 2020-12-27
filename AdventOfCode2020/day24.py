positions = {
    'w': (-1, 0),
    'e': (1, 0),
    'nw': (-1, -1),
    'ne': (0, -1),
    'sw': (-1, 1),
    'se': (0, 1)
}


def count_black_tiles(x, y):
    adjacent = [(x, y) for x, y in positions.values()]
    if y % 2 == 1:
        adjacent = [(-1, 0), (1, 0), (0, -1), (1, -1), (0, 1), (1, 1)]
    return len(([(dx + x, dy + y) for dx, dy in adjacent
                 if (dx + x, dy + y) in black]))


with open('input-day24.txt', 'r') as f:
    movements = [line.strip() for line in f.readlines()]
    dict = {}
    for move in movements:
        x, y = (0, 0)
        move = move.replace('e', 'e,').replace('w', 'w,')
        directions = sorted(move.strip(',').split(','))
        for direction in directions:
            x += positions[direction][0]
            y += positions[direction][1]
            if direction not in ('e', 'w') and y % 2 == 0:
                x += 1
        if (x, y) not in dict:
            dict[(x, y)] = 1
        else:
            dict[(x, y)] += 1

    black = sorted([x for x, y in dict.items() if y % 2 == 1])
    dict_black = {tile: 1 for tile in black}
    print(f'part 1:', len(black))

    for _ in range(100):
        min_x, max_x = min(x for x, _ in black), max(x for x, _ in black)
        min_y, max_y = min(y for _, y in black), max(y for _, y in black)
        flip = {}
        unflip = {}
        for x, y in black:
            if count_black_tiles(x, y) not in (1, 2):
                unflip[(x, y)] = 1

        for x in range(min_x - 1, max_x + 2):
            for y in range(min_y - 1, max_y + 2):
                if (x, y) not in black and count_black_tiles(x, y) == 2:
                    flip[(x, y)] = 1

        black = set(black).union(set(flip.keys())).difference(
            set(unflip.keys()))

    print(f'part 2:', len(black))