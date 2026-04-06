#
# @lc app=leetcode id=57 lang=python3
#
# [57] Insert Interval
#

# @lc code=start
class Solution:
    def insert(self, intervals: List[List[int]], newInterval: List[int]) -> List[List[int]]:
        result = []
        for interval in intervals:
            if newInterval[1] < interval[0]:
                result.append(newInterval)
                return result + intervals[intervals.index(interval):]
            elif newInterval[0] > interval[1]:
                result.append(interval)
            else:
                newInterval = [min(newInterval[0], interval[0]), max(newInterval[1], interval[1])]
        result.append(newInterval)
        return result
# @lc code=end