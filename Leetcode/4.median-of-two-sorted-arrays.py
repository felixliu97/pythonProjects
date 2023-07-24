#
# @lc app=leetcode id=4 lang=python3
#
# [4] Median of Two Sorted Arrays
#

# @lc code=start
class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        join = nums1 + nums2
        join.sort()
        size = len(join)
        mid = int(size/2)
        if size % 2 != 0:
            return join[mid]
        else:
            return (join[mid-1]+join[mid])/2
        
# @lc code=end

