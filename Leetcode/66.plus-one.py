#
# @lc app=leetcode id=66 lang=python3
#
# [66] Plus One
#

# @lc code=start
class Solution:
    def plusOne(self, digits: List[int]) -> List[int]:
        num = int(''.join([str(d) for d in digits]))
        return [int(d) for d in str(num+1)]
        
# @lc code=end

