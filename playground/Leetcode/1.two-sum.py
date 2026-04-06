#
# @lc app=leetcode id=1 lang=python3
#
# [1] Two Sum
#

# @lc code=start
class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        dict = {}
        for index, num in enumerate(nums):
            complement = target - num
            if complement in dict:
                return [dict[complement], index]
            dict[num] = index

# @lc code=end

