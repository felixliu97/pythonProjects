#
# @lc app=leetcode id=18 lang=python3
#
# [18] 4Sum
#

# @lc code=start
class Solution:
    def fourSum(self, nums: List[int], target: int) -> List[List[int]]:
        nums.sort()
        results = []
        for i in range(len(nums) - 3):
            if i > 0 and nums[i] == nums[i-1]:
                continue
            for j in range(i+1, len(nums)-2):
                if j > i+1 and nums[j] == nums[j-1]:
                    continue
                k, l = j+1, len(nums)-1
                while k < l:
                    sum = nums[i] + nums[j] + nums[k] + nums[l]
                    if sum == target:
                        results.append([nums[i],nums[j],nums[k],nums[l]])
                        while k < l and nums[k] == nums[k+1]:
                            k += 1
                        while k < l and nums[l] == nums[l-1]:
                            l -= 1
                        k += 1
                        l -= 1
                    elif sum < target:
                        k += 1
                    else:
                        l -= 1
        return results
        # nums.sort()
        # results = []
        # for a in range(len(nums)-3):
        #     if a > 0 and nums[a] == nums[a-1]:
        #         continue
        #     for b in range(a+1, len(nums)-2):
        #         c = b+1
        #         d = len(nums)-1
        #         while c < d:
        #             sum = nums[a] + nums[b] + nums[c] + nums[d]
        #             if sum == target:
        #                 results.append([nums[a], nums[b], nums[c], nums[d]])
        #                 while c < d and nums[c] == nums[c+1]:
        #                     c += 1
        #                 while c < d and nums[d] == nums[d-1]:
        #                     d -= 1
        #                 c += 1
        #                 d -= 1
        #             elif sum < target:
        #                 c += 1
        #             else:
        #                 d -= 1
        # return results
        
# @lc code=end

