#
# @lc app=leetcode id=45 lang=python3
#
# [45] Jump Game II
#

# @lc code=start
class Solution:
    def jump(self, nums: List[int]) -> int:
        # size of list
        n = len(nums)
        jump, current_end, farthest = 0, 0, 0
        for i in range(n-1):
            farthest = max(farthest, i + nums[i])
            if i == current_end:
                jump += 1
                current_end = farthest
            # print(f"i:{i}, farthest:{farthest}, jump:{jump}, current_end:{current_end}")
        return jump
        
# @lc code=end

