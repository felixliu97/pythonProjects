#
# @lc app=leetcode id=16 lang=python3
#
# [16] 3Sum Closest
#

# @lc code=start
class Solution:
    def threeSumClosest(self, nums: List[int], target: int) -> int:
        # three pointers
        n = len(nums)
        nums.sort()
        minDiff = 13001
        val = 0
        for left in range(n):
            mid = left + 1
            right = n - 1
            while(mid < right):
                sum = nums[left] + nums[mid] + nums[right]
                diff = abs(sum - target)
                if(diff < minDiff):
                    minDiff = diff
                    val = sum
                if(sum == target):
                    return target
                elif(sum < target):
                    mid += 1
                else:
                    right -= 1
            
        return val
# @lc code=end

