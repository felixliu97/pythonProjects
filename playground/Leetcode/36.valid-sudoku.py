#
# @lc app=leetcode id=36 lang=python3
#
# [36] Valid Sudoku
#

# @lc code=start
class Solution:
    def isValidSudoku(self, board: List[List[str]]) -> bool:
        # check rows
        for row in board:
            filled = [x for x in row if x != '.']
            if len(filled) != len(set(filled)):
                return False
        # check columns
        for col in range(9):
            filled = []
            for row in board:
                if row[col] != '.':
                    filled.append(row[col])
            if len(filled) != len(set(filled)):
                return False
        # check sub-boxes
        for row in range(0,9,3):
            for col in range(0,9,3):
                filled = []
                for i in range(3):
                    for j in range(3):
                        cell = board[row+i][col+j]
                        if cell != '.':
                            filled.append(cell)
                if len(filled) != len(set(filled)):
                    return False
        return True
            

        
# @lc code=end

