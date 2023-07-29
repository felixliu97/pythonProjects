#
# @lc app=leetcode id=19 lang=python3
#
# [19] Remove Nth Node From End of List
#

# @lc code=start
# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def removeNthFromEnd(self, head: Optional[ListNode], n: int) -> Optional[ListNode]:
        # create a duplicate
        dummy = ListNode()
        dummy.next = head

        p1, p2 = dummy, head
        # p2 is ahead of p1 by n+1 nodes
        for _ in range(n):
            p2 = p2.next

        # when p2 reaches end, p1 is at (n+1)th last node
        while p2:
            p1, p2 = p1.next, p2.next
        
        # remove nth last node
        p1.next = p1.next.next
        return dummy.next
        
# @lc code=end

