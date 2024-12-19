#
# @lc app=leetcode id=45 lang=python3
#
# [45] Jump Game II
#

# @lc code=start
class Solution:
    def jump(self, nums: List[int]) -> int:
        n = len(nums)
        dp = [float('inf')] * n
        dp[n-1] = 0

        for i in range(n-2,-1,-1):
            for j in range(1, min(nums[i]+1, n-i)):
                dp[i] = min(dp[i], dp[i+j]+1)
                # print(f"i:{i},j:{j},nums[i]:{nums[i]},n-i:{n-i}")
                # print(dp)
        return dp[0]
        
# @lc code=end

