#
# @lc app=leetcode id=210 lang=python3
#
# [210] Course Schedule II
#
from collections import defaultdict, deque
# @lc code=start
class Solution:
    def findOrder(self, numCourses: int, prerequisites: List[List[int]]) -> List[int]:
        # graph = defaultdict(list)
        # for course, prereq in prerequisites:
        #     graph[course].append(prereq)
        
        # visited = [0] * numCourses
        # result = []
        
        # def dfs(course):
        #     if visited[course] == -1:
        #         return False
        #     if visited[course] == 1:
        #         return True
            
        #     visited[course] = -1
        #     for prereq in graph[course]:
        #         if not dfs(prereq):
        #             return False
            
        #     visited[course] = 1
        #     result.append(course)
        #     return True
        
        # for course in range(numCourses):
        #     if not dfs(course):
        #         return []
        
        # return result
        graph = defaultdict(list)
        in_degree = [0] * numCourses
        print(in_degree)
        for course, prereq in prerequisites:
            # print(f"course:{course}, prereq:{prereq}")
            graph[prereq].append(course)
            in_degree[course] += 1

        queue = deque([c for c in range(numCourses) if in_degree[c] == 0])
        # print(queue)
        result = []
        while queue:
            course = queue.popleft()
            result.append(course)
            for prereq in graph[course]:
                in_degree[prereq] -= 1
                if in_degree[prereq] == 0:
                    queue.append(prereq)
        return result if len(result) == numCourses else []


# @lc code=end

