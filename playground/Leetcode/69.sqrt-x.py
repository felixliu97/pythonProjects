#
# @lc app=leetcode id=69 lang=python3
#
# [69] Sqrt(x)
#

# @lc code=start
class Solution:
    def mySqrt(self, x: int) -> int:
        if x == 1:
            return x

        left, right = 1, x
        result = 0

        while left <= right:
            mid = left + (right - left) // 2
            square = mid * mid

            if square == x:
                return mid
            elif square < x:
                left = mid + 1
                result = mid  # Update result as we need floor value
            else:
                right = mid - 1

        return result
        
# @lc code=end

