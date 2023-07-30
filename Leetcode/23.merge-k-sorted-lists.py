#
# @lc app=leetcode id=23 lang=python3
#
# [23] Merge k Sorted Lists
#

# @lc code=start
# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def mergeKLists(self, lists: List[Optional[ListNode]]) -> Optional[ListNode]:
        head = temp = ListNode()
        res = []

        for ls in lists:
            while ls:
                res.append(ls.val)
                ls = ls.next

        for val in sorted(res):
            temp.next = ListNode()
            temp = temp.next
            temp.val = val

        return head.next
# @lc code=end

