#
# @lc app=leetcode id=11 lang=python3
#
# [11] Container With Most Water
#

# @lc code=start
class Solution:
    def maxArea(self, height: List[int]) -> int:
        #two pointers
        left = 0
        right = len(height) - 1
        maxArea = 0

        while left < right:
            currentArea = min(height[left], height[right]) * (right - left)
            maxArea = max(currentArea, maxArea)
            if height[left] > height[right]:
                right -= 1
            else:
                left += 1

        return maxArea
        
# @lc code=end

