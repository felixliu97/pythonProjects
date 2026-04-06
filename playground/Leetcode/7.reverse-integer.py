#
# @lc app=leetcode id=7 lang=python3
#
# [7] Reverse Integer
#

# @lc code=start
class Solution:
    def reverse(self, x: int) -> int:
        if x >= 0:
            y = int(str(x)[::-1])
            return y if y <= 2**31-1 else 0
        
        else: 
            y = -int(str(x)[:0:-1])
            return y if y >= -2**31 else 0
        
# @lc code=end

