#
# @lc app=leetcode id=6 lang=python3
#
# [6] Zigzag Conversion
#

# @lc code=start
class Solution:
    def convert(self, s: str, numRows: int) -> str:
        if numRows >= len(s) or numRows == 1:
            return s
        dict = {}
        cur,increment = 0,1
        for c in s:
            if cur not in dict:
                dict[cur] = []
            dict[cur].append(c)
            if (increment > 0 and cur == (numRows-1)) or (increment < 0 and cur == 0):
                increment *= -1
            cur += increment
        result = ""
        for i in range(numRows):
            s = "".join(dict[i])
            result += s
        return result
        
# @lc code=end

