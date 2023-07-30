#
# @lc app=leetcode id=22 lang=python3
#
# [22] Generate Parentheses
#

# @lc code=start
class Solution:
    def generateParenthesis(self, n: int) -> List[str]:
        def get_str(res, s, left, right):
            # if no left or right bracket
            if left == 0 and right == 0:
                res.append(s)
                return
            # if left bracket
            if left > 0:
                get_str(res, s+'(', left-1, right)
            # if right bracket
            if right > 0 and left < right:
                get_str(res, s+')', left, right-1)
        
        res = []
        get_str(res, '', n, n)

        return res
        
# @lc code=end

