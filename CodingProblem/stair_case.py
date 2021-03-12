# recursive
def staircase(n):
    if n <= 1:
        return 1
    return staircase(n - 1) + staircase(n - 2)

print("staircase() has {} ways for {} stairs".format(staircase(7), 7))

# faster algorithm
def staircase2(n):
    a, b = 1, 2
    for x in range(n - 1):
        a, b = b, a + b
    return a

print("staircase2() has {} ways for {} stairs".format(staircase2(7), 7))

# recursive from a list of steps
def staircase3(n, S):
    if n < 0:
        return 0
    elif n == 0:
        return 1
    else:
        return sum(staircase3(n - x, S) for x in S)

S = {1, 3, 5}
print("staircase3() has {} ways for {} stairs".format(staircase3(8,S), 8))

# dynamic programming, store cache to avoid repeated computations
def staircase4(n, S):
    cache = [0 for i in range(n + 1)]
    # print(cache)
    cache[0] = 1
    # print(cache)
    for i in range(1, n + 1):
        # print(i)
        cache[i] += sum(cache[i - x] for x in S if i - x >= 0)
        # print(cache)
    return cache[n]

T = {1, 3, 5}
print("staircase4() has {} ways for {} stairs".format(staircase4(8,T), 8))