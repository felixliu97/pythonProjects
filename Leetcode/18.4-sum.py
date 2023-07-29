#
# @lc app=leetcode id=18 lang=python3
#
# [18] 4Sum
#

# @lc code=start
class Solution:
    def fourSum(self, nums: List[int], target: int) -> List[List[int]]:
        nums.sort()
        result = set()
        # list size
        L = len(nums)
        # larget number
        R = nums[-1]
        # first number
        for i in range(L-3):
            a = nums[i]
            # go to next number
            if a + 3*R < target: continue
            # no result
            if 4*a > target: break
            # second number
            for j in range(i+1, L-2):
                b = nums[j]
                # go to next number
                if a + b + 2*R < target: continue
                # no result
                if a + 3*b > target: break
                # third number
                for k in range(j+1, L-1):
                    c = nums[k]
                    # fourth number
                    d = target - (a+b+c)
                    # go to next number
                    if d > R: continue
                    # no result
                    if d < c: break
                    if d in nums[k+1:]:
                        result.add((a,b,c,d))
        return result
        
# @lc code=end

