#
# @lc app=leetcode id=29 lang=python3
#
# [29] Divide Two Integers
#
import math
# @lc code=start
class Solution:
    def divide(self, dividend: int, divisor: int) -> int:
        if dividend * divisor < 0:
            return max(math.ceil(dividend/divisor), -2**31)
        else:
            return min(math.floor(dividend/divisor), 2**31-1)
        
# @lc code=end

