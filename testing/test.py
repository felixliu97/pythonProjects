# Define a Node class to represent a node in a binary tree
class Node:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right

# Define a function to return all paths from the root to leaves in a binary tree
def get_paths(root):
    # If the root is None, return an empty list
    if root is None:
        return []

    # If the root is a leaf, return a list containing the path to the leaf
    if root.left is None and root.right is None:
        return [[root.value]]

    # Get the paths from the left and right subtrees
    left_paths = get_paths(root.left)
    right_paths = get_paths(root.right)

    # Concatenate the root value to each path from the left and right subtrees
    left_paths = [[root.value] + path for path in left_paths]
    right_paths = [[root.value] + path for path in right_paths]

    # Return the concatenated list of paths
    return left_paths + right_paths

# Define a binary tree
tree = Node(1, Node(2, Node(4), Node(5)), Node(3, Node(6), Node(7)))

# Get all paths from the root to leaves
paths = get_paths(tree)

# Print the paths
print(paths) # prints: [[1, 2, 4], [1, 2, 5], [1, 3, 6], [1, 3, 7]]
