#
# @lc app=leetcode id=18 lang=python3
#
# [18] 4Sum
#

# @lc code=start
class Solution:
    def fourSum(self, nums: List[int], target: int) -> List[List[int]]:
        nums.sort()
        n = len(nums)
        result = []
        for i in range(n-3): # first number
            if nums[i] > target/4:
                break
            if (i > 0 and nums[i] == nums[i-1]): # skip same first number
                continue
            for j in range(i+1,n-2): # second number
                if j > i+1 and nums[j] == nums[j-1]:
                    continue # skip same second number
                k = j+1 # third number
                l = n-1 # fourth number
                while k < l:
                    current_sum = nums[i] + nums[j] + nums[k] + nums[l]
                    if current_sum == target:
                        result.append([nums[i],nums[j],nums[k],nums[l]])
                        while k < l and nums[k] == nums[k+1]: # skip same third number
                            k += 1
                        while k < l and nums[l] == nums[l-1]: # skip same fourth number
                            l -= 1
                        k += 1
                        l -= 1
                    elif current_sum > target:
                        l -= 1
                    else:
                        k += 1
        return result
        
# @lc code=end

