#
# @lc app=leetcode id=94 lang=python3
#
# [94] Binary Tree Inorder Traversal
#

# @lc code=start
# Definition for a binary tree node.
# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right
class Solution:
    def inorderTraversal(self, root: Optional[TreeNode]) -> List[int]:
        result = []
        def inorder(node):
            if node:
                # Traverse left subtree
                inorder(node.left)
                # Visit the root
                result.append(node.val)
                # Traverse right subtree
                inorder(node.right)
        
        inorder(root)
        return result
        
# @lc code=end

