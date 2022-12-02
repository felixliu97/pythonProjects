def count_flip(s:str):
    x = s.rstrip('y')
    return x.count('y')

tests = {
    'xyxxxyxyy' : 2
    ,'xxxxxyxyy' : 1
    ,'xxyyyx':3
}

for key, val in tests.items():
    print(f"Asserting count_flip('{key}') == {val}")
    assert(count_flip(key) == val)