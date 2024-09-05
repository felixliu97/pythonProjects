#
# @lc app=leetcode id=67 lang=python3
#
# [67] Add Binary
#

# @lc code=start
class Solution:
    def addBinary(self, a: str, b: str) -> str:
        # Convert binary strings to integers
        num1 = int(a, 2)
        num2 = int(b, 2)
        
        # Add the integers
        sum_int = num1 + num2
        
        # Convert the sum back to binary string
        return bin(sum_int)[2:]  # [2:] removes the '0b' prefix
        
# @lc code=end

