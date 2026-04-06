def move(cups, max_num, iterations):

    for _ in range(iterations):
        current_cup = cups[0]
        # print(f'current cup:', current_cup)

        pick_up = cups[1:4]
        # print(f'pick up:', pick_up)

        destination = current_cup - 1 if current_cup > 1 else max_num
        while destination in pick_up:
            destination = destination - 1 if destination > 1 else max_num

        destination_index = cups.index(destination)
        # print(f'destination:', destination, destination_index)

        cups = cups[4:destination_index +
                    1] + pick_up + cups[destination_index + 1:] + cups[0:1]
        # print(f'cups:', cups)
    return cups


def move2(cups, max_num, iterations):
    dict = {cups[i]: i % max_num for i in range(max_num)}
    print(dict)


cups = [int(x) for x in '586439172']
# print(f'original:', cups)

print(f'part 1:', move(cups, 9, 100))

new_cups = cups + list(range(max(cups) + 1, 201))
# new_cups = move(new_cups, 1000000, 10000000)

move2(new_cups, 200, 100)

# print(new_cups.index(1))
