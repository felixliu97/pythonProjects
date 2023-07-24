#
# @lc app=leetcode id=15 lang=python3
#
# [15] 3Sum
#

# @lc code=start
class Solution:
    def threeSum(self, nums: List[int]) -> List[List[int]]:
        # three pointers
        nums.sort()

        result = []
        n = len(nums)

        left = 0
        # iterate through the list with left
        while left < n - 2:
            # skip over duplicates of nums[left]
            if left > 0 and nums[left] == nums[left - 1]:
                left += 1
                continue

            # exit early if nums[left] is greater than 0
            if nums[left] > 0:
                break

            # set mid and right
            mid, right = left + 1, n - 1

            while mid < right:
                # check for sum of 0
                sum = nums[left] + nums[mid] + nums[right]
                if sum == 0:
                    result.append([nums[left], nums[mid], nums[right]])
                    mid += 1
                    right -= 1

                    # skip over duplicates of nums[mid]
                    while mid < right and nums[mid] == nums[mid - 1]:
                        mid += 1

                    # skip over duplicates of nums[right]
                    while mid < right and nums[right] == nums[right + 1]:
                        right -= 1

                # adjust mid or right based on sum
                elif sum < 0:
                    mid += 1
                else:
                    right -= 1

            left += 1

        return result
        
# @lc code=end

