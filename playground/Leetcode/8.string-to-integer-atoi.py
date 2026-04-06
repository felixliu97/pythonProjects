#
# @lc app=leetcode id=8 lang=python3
#
# [8] String to Integer (atoi)
#
import re
# @lc code=start
class Solution:
    def myAtoi(self, s: str) -> int:
        match = re.search(r'^[ ]*([-|+]?\d+)', s)
        if match:
            num = int(match.group(1).lstrip('+'))
            if num <= 0:
                return max(-2**31, num)
            else:
                return min(2**31-1, num)
        return 0
# @lc code=end

