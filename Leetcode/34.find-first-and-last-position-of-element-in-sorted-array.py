#
# @lc app=leetcode id=34 lang=python3
#
# [34] Find First and Last Position of Element in Sorted Array
#

# @lc code=start
class Solution:
    def searchRange(self, nums: List[int], target: int) -> List[int]:
        try:
            # Find the first occurrence
            first_index = nums.index(target)
            # Find the last occurrence by reversing the list
            last_index = len(nums) - 1 - nums[::-1].index(target)
            return [first_index, last_index]
        except:
            # If element is not found
            return [-1, -1]

# @lc code=end

