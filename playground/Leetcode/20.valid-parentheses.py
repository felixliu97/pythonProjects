#
# @lc app=leetcode id=20 lang=python3
#
# [20] Valid Parentheses
#

# @lc code=start
class Solution:
    def isValid(self, s: str) -> bool:
        l = []
        for c in s:
            if c in ('(','[','{'):
                l.append(c)
            else:
                if not l or (c == ')' and l[-1] != '(') or (c == ']' and l[-1] != '[') or (c == '}' and l[-1] != '{'):
                    return False
                l.pop()
        return len(l) == 0

            
# @lc code=end

