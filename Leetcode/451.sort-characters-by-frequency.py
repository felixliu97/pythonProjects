#
# @lc app=leetcode id=451 lang=python3
#
# [451] Sort Characters By Frequency
#
from collections import Counter
# @lc code=start
class Solution:
    def frequencySort(self, s: str) -> str:
        freq = Counter(s)
        sorted_char = sorted(freq, key=lambda x: freq[x], reverse=True)
        return ''.join(c * freq[c] for c in sorted_char)
        
# @lc code=end

