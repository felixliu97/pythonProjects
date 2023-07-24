from itertools import combinations

def unique_combinations(lst):
    for pair in combinations(lst, 2):
        print(pair)
        print(pair[0], pair[1])

# Example usage
my_list = [3, 2, 1, 4, 5]
unique_combinations(my_list)
