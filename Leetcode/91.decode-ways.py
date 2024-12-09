#
# @lc app=leetcode id=91 lang=python3
#
# [91] Decode Ways
#

# @lc code=start
class Solution:
    def numDecodings(self, s: str) -> int:
        n = len(s)
        dp = [0] * (n + 1)
        
        # Base cases
        dp[0] = 1
        dp[1] = 1 if s[0] != '0' else 0
        
        for i in range(2, n + 1):
            # Single digit
            single_digit = int(s[i-1])
            if single_digit != 0:
                dp[i] += dp[i-1]
            
            # Two digits
            two_digits = int(s[i-2:i])
            if 10 <= two_digits <= 26:
                dp[i] += dp[i-2]
        
        return dp[n]
    
# @lc code=end

