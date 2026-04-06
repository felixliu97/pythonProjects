#
# @lc app=leetcode id=35 lang=python3
#
# [35] Search Insert Position
#

# @lc code=start
class Solution:
    def searchInsert(self, nums: List[int], target: int) -> int:
        for idx, num in enumerate(nums):
            if num >= target:
                return idx
        return idx+1
# @lc code=end

