#
# @lc app=leetcode id=210 lang=python3
#
# [210] Course Schedule II
#
from collections import defaultdict, deque
# @lc code=start
class Solution:
    def findOrder(self, numCourses: int, prerequisites: List[List[int]]) -> List[int]:
        dict = defaultdict(list)
        visited = [0] * numCourses
        for course, pre in prerequisites:
            dict[pre].append(course)
            visited[course] += 1
        queue = deque([c for c in range(numCourses) if visited[c] == 0])
        result = []
        while queue:
            course = queue.popleft()
            result.append(course)
            for pre in dict[course]:
                visited[pre] -= 1
                if visited[pre] == 0:
                    queue.append(pre)
        return result if len(result) == numCourses else []


# @lc code=end

