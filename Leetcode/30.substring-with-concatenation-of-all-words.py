#
# @lc app=leetcode id=30 lang=python3
#
# [30] Substring with Concatenation of All Words
#

# @lc code=start
class Solution:
    def findSubstring(self, s: str, words: List[str]) -> List[int]:
        if not words: return []
        words.sort()
        res = []
        word_len = len(words[0])
        words_len = len(words)*len(words[0])
        for i in range(len(s) - words_len + 1):
            if words == sorted([s[i+j*word_len:i+(j+1)*word_len] for j in range(len(words))]):
                res.append(i)
        return res
        
# @lc code=end

