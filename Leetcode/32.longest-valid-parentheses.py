#
# @lc app=leetcode id=32 lang=python3
#
# [32] Longest Valid Parentheses
#

# @lc code=start
class Solution:
    def longestValidParentheses(self, s: str) -> int:
        stack = [-1]
        max_len = 0
        for i, c in enumerate(s):
            if c == '(':
                stack.append(i)
            else:
                stack.pop()
                # reset starting point
                if not stack:
                    stack.append(i)
                # update max_len
                else:
                    max_len = max(max_len, i - stack[-1])
            print(stack, max_len)
        return max_len
        
# @lc code=end

