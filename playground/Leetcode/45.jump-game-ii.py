#
# @lc app=leetcode id=45 lang=python3
#
# [45] Jump Game II
#

# @lc code=start
class Solution:
    def jump(self, nums: List[int]) -> int:
        # greedy
        n = len(nums)
        jumps, current_max, next_max = 0,0,0
        for i in range(n-1):
            next_max = max(next_max, nums[i] + i)
            if i == current_max:
                jumps += 1
                current_max = next_max
                if current_max >= n-1:
                    break
        return jumps
        # dynamic programming
        # n = len(nums)
        # dp = [float('inf')] * n
        # dp[0] = 0

        # for i in range(n):
        #     # Try all possible jumps from position i
        #     for j in range(1, nums[i] + 1):
        #         if i + j < n:
        #             # Update with minimum jumps
        #             dp[i + j] = min(dp[i + j], dp[i] + 1)
        
        # return dp[n - 1]
        
# @lc code=end

