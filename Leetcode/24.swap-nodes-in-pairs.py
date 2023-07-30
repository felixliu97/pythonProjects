#
# @lc app=leetcode id=24 lang=python3
#
# [24] Swap Nodes in Pairs
#

# @lc code=start
# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def swapPairs(self, head: Optional[ListNode]) -> Optional[ListNode]:
        if not (head and head.next): return head
        # 2nd element become head
        newHead = head.next
        # swap next 2 elements
        head.next, newHead.next = self.swapPairs(head.next.next), head
        return newHead
# @lc code=end

