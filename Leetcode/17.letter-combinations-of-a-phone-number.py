#
# @lc app=leetcode id=17 lang=python3
#
# [17] Letter Combinations of a Phone Number
#
import itertools
# @lc code=start
class Solution:
    def letterCombinations(self, digits: str) -> List[str]:
        dict = {"2": "abc", "3": "def", "4": "ghi", "5": "jkl", "6": "mno", "7": "pqrs", "8": "tuv", "9": "wxyz"}
        all_lists = []
        for digit in digits:
            all_lists.append([l for l in dict[digit]])
        return [] if len(all_lists) == 0 else ["".join(letters) for letters in itertools.product(*all_lists)]
        
# @lc code=end

