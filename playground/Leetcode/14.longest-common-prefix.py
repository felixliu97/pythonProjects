#
# @lc app=leetcode id=14 lang=python3
#
# [14] Longest Common Prefix
#

# @lc code=start
class Solution:
    def longestCommonPrefix(self, strs: List[str]) -> str:
        prefix = min(strs, key=len)
        for str in strs:
            while not str.startswith(prefix):
                prefix = prefix[:-1]
            if not prefix:
                return ""
        return prefix
    
        
# @lc code=end

