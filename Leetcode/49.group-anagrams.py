#
# @lc app=leetcode id=49 lang=python3
#
# [49] Group Anagrams
#
from collections import defaultdict
# @lc code=start
class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        group = defaultdict(list)
        for str in strs:
            key = ''.join(sorted(str))
            group[key].append(str)
        return list(group.values())
            
        
# @lc code=end

