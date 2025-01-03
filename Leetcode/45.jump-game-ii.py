#
# @lc app=leetcode id=45 lang=python3
#
# [45] Jump Game II
#

# @lc code=start
class Solution:
    def jump(self, nums: List[int]) -> int:
        n = len(nums)
        jumps,current_max,next_max = 0,0,0
        for i in range(n-1):
            next_max = max(next_max, nums[i] + i)
            if i == current_max:
                jumps += 1
                current_max = next_max
        return jumps
        
# @lc code=end

