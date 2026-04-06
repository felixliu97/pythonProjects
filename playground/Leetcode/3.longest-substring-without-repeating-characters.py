#
# @lc app=leetcode id=3 lang=python3
#
# [3] Longest Substring Without Repeating Characters
#

# @lc code=start
class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        seen = {}
        left = max_len = 0
        for right, cur in enumerate(s):
            if cur in seen:
                left = max(left, seen[cur] + 1)
            max_len = max(max_len, right - left + 1)
            seen[cur] = right
        return max_len
# @lc code=end

