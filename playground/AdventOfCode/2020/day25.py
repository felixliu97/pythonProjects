def loop_size(key):
    subject, number, loop_size = 7, 1, 0
    while number != key:
        number *= subject
        number = number % 20201227
        loop_size += 1
    return loop_size


def encryption_key(key, loop_size):
    number = 1
    for _ in range(loop_size):
        number *= key
        number = number % 20201227
    return number


with open('input-day25.txt', 'r') as f:
    card, door = [int(x) for x in f.read().strip().split('\n')]
    print(card, door)

    card_loop_size = loop_size(card)
    print(encryption_key(door, card_loop_size))