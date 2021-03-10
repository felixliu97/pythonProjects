stones = [1, 1, 3, 3, 2, 1]

def getCost(list):
    highest = max(stones)
    i, occurence = highest, 1

    print(f"Highest Number:", highest)

    while i > 0:
        if len([1 for n in list if n >= i]) >= occurence:
            occurence += 2
        else:
            highest -= 1
        i -= 1

    print(f"Highest Stone:", highest)

    return sum(list) - sum(range(highest)) * 2 - highest

print(f"Cost:", getCost(stones))
