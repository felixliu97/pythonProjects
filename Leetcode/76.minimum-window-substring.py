#
# @lc app=leetcode id=76 lang=python3
#
# [76] Minimum Window Substring
#
from collections import Counter
# @lc code=start
class Solution:
    def minWindow(self, s: str, t: str) -> str:
        need = Counter(t)
        missing = len(t)
        left = start = end = 0
        for right, char in enumerate(s, 1):
            if need[char] > 0:
                missing -= 1
            need[char] -= 1
            if not missing:
                while left < right and need[s[left]] < 0: # proceed to 
                    need[s[left]] += 1
                    left += 1
                if not end or right - left < end - start:
                    start, end = left, right
        return s[start:end]
        
# @lc code=end

