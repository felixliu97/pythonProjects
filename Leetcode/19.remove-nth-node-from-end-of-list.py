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
        dummy = ListNode()
        dummy.next = head

        slow, fast = dummy, head
        for _ in range(n):
            fast = fast.next

        # when fast reaches end, slow is at (n+1)th last node
        while fast:
            fast, slow = fast.next, slow.next

        slow.next = slow.next.next
        return dummy.next
        
# @lc code=end

