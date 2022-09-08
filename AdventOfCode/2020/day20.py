with open('input-day20.txt', 'r') as f:
    tiles = f.read().strip().split('\n\n')
    for tile in tiles:
        rows = tile.split('\n')
        left, right = '', ''
        top = rows[1]
        bottom = rows[-1]
        for row in rows:
            if 'Tile' in row:
                tile_number = int(row.split()[1].strip(':'))
                print(tile_number)
            else:
                left += row[0]
                right += row[-1]

        print(f'top:', top)
        print(f'left:', left)
        print(f'bottom:', bottom)
        print(f'right:', right)