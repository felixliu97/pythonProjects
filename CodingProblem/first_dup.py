def find_first_duplicate(nums):
    num_dict = {}
    for num in nums:
        if num not in num_dict:
            num_dict[num] = 1
        else:
            return num
    return None

l = [1,2,3,5,5,4,4]
print(f"First duplicate: {find_first_duplicate(l)}")