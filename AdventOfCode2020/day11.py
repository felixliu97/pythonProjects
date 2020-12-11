adjacent = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

def countOccupied(seats, row, col):
    rows = len(seats)
    cols = len(seats[0])
    return len([seats[row + dx][col + dy] for dx, dy in adjacent if 0 <= row + dx < rows and 0 <= col + dy < cols and seats[row + dx][col + dy] == '#'])

def countOccupiedLine(seats, row, col):
    rows = len(seats)
    cols = len(seats[0])
    occupied = 0
    for dx, dy in adjacent:
        new_row, new_col = row + dx, col + dy
        while (0 <= new_row < rows and 0 <= new_col < cols):
            if seats[new_row][new_col] == '#':
                occupied += 1
                break
            if seats[new_row][new_col] == 'L':
                break
            new_row += dx
            new_col += dy
    return occupied

def checkSeats(seats, method):
    check_seats = ['' for seat in seats]
    rows = len(seats)
    cols = len(seats[0])
    for i in range(rows):
        row = ''
        for j in range(cols):
            if seats[i][j] == 'L' and ((method == 'adjacent' and countOccupied(seats, i, j) == 0) or (method == 'line' and countOccupiedLine(seats, i, j) == 0)):
                    row += '#'
            elif seats[i][j] == '#' and ((method == 'adjacent' and countOccupied(seats, i, j) >= 4) or (method == 'line' and countOccupiedLine(seats, i, j) >= 5)):
                row += 'L'
            else:
                row += seats[i][j]
        check_seats[i] = row
    return check_seats

def changeSeats(seats, method):
    oldseats = seats
    newseats = checkSeats(seats, method)
    while oldseats != newseats:
        oldseats = newseats
        newseats = checkSeats(oldseats, method)
    occupied = [seat.count('#') for seat in newseats]
    return sum(occupied)

with open('input-day11.txt', 'r') as f:
    seats = [line.strip() for line in f.readlines()]
    print(f'Part 1:',changeSeats(seats, 'adjacent'))
    print(f'Part 2:',changeSeats(seats, 'line'))
