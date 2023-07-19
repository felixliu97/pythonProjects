#
# @lc app=leetcode id=14 lang=python3
#
# [14] Longest Common Prefix
#

# @lc code=start
class Solution:
    def longestCommonPrefix(self, strs: List[str]) -> str:
        pre = min(strs, key=len)
        for str in strs:
            while not str.startswith(pre):
                pre = pre[:-1]
        return pre     
        
# @lc code=end

