#
# @lc app=leetcode id=84 lang=python3
#
# [84] Largest Rectangle in Histogram
#

# @lc code=start
class Solution:
    def largestRectangleArea(self, heights: List[int]) -> int:
        n = len(heights)
        if n == 0:
            return 0
        max_area = 0
        for i in range(n):
            left = right = i
            while left > 0 and heights[left - 1] >= heights[i]:
                left -= 1
            while right < n - 1 and heights[right + 1] >= heights[i]:
                right += 1
            max_area = max(max_area, heights[i] * (right - left + 1))
        return max_area

# @lc code=end

