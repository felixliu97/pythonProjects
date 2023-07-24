#
# @lc app=leetcode id=10 lang=python3
#
# [10] Regular Expression Matching
#
import re
# @lc code=start
class Solution:
    def isMatch(self, s: str, p: str) -> bool:
        match = re.match(f"^{p}$", s)
        return True if match else False
# @lc code=end

