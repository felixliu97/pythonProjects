def factorial(n):
    result = 1
    while n > 1:
        result *= n
        n -= 1

    return result

def throw_dice(N, faces, total):
    assert(N >= 1 and faces >= 1 and total >= 1)

    if total > N * faces or total < N:
        return 0

    return int(factorial(total - 1) / (factorial(N - 1) * factorial(total - N)))

print(throw_dice(3, 6, 7))