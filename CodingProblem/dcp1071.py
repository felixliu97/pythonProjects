S = [12, 1, 61, 5, 9, 2]
k = 24

def returnSubset(data, target:int):
    if len(data) == 0:
        return None
    if len(data) == 1 and data[0] == target:
        return data
    raw = data
    raw.sort()
    print(f"raw: {raw}")


returnSubset(S, k)
