#
# @lc app=leetcode id=13 lang=python3
#
# [13] Roman to Integer
#

# @lc code=start
class Solution:
    def romanToInt(self, s: str) -> int:
        values = {'I':1,'V':5,'X':10,'L':50,'C':'100','D':500,'M':1000}
        s = s.replace('IV','IIII') \
            .replace('IX','VIIII') \
            .replace('XL','XXXX') \
            .replace('XC','LXXXX') \
            .replace('CD','CCCC') \
            .replace('CM','DCCCC')
        sum = 0
        for l in s:
            sum += int(values[l])
        return sum
        
# @lc code=end

