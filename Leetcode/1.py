def twoSum(nums, target):
    """
    :type nums: List[int]
    :type target: int
    :rtype: List[int]
    """
    visited = {}
    for i, num in enumerate(nums):
        reminder = target - nums[i]
        if reminder in visited:
            return [visited[reminder], i]
        visited[num] = i
        

nums = [2,7,11,15]
target = 9
print(f"nums = {nums}, target = {target}, result: {twoSum(nums, target)}")

nums = [3,2,4]
target = 6
print(f"nums = {nums}, target = {target}, result: {twoSum(nums, target)}")

nums = [3,3]
target = 6
print(f"nums = {nums}, target = {target}, result: {twoSum(nums, target)}")