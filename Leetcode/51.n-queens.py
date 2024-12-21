#
# @lc app=leetcode id=51 lang=python3
#
# [51] N-Queens
#

# @lc code=start
class Solution:
    def solveNQueens(self, n: int) -> List[List[str]]:
        # Start with an empty n x n chessboard.
        # Place a queen in the first column of the first row.
        # Move to the next column and try to place a queen in a safe position.
        # If a safe position is found, move to the next column. If not, backtrack to the previous column and try a different position.
        # Repeat steps 3-4 until all n queens are placed or all possibilities are exhausted.
        def is_safe(row, col):
            # Check row on left side
            for i in range(col):
                if board[row][i] == 'Q':
                    return False
            # Check upper diagonal on left side
            for i, j in zip(range(row, -1, -1), range(col, -1, -1)):
                if board[i][j] == 'Q':
                    return False
            # Check lower diagonal on left side
            for i, j in zip(range(row, n, 1), range(col, -1, -1)):
                if board[i][j] == 'Q':
                    return False
            return True

        def backtrack(col):
            if col == n:
                results.append([''.join(row) for row in board])
                return
            for row in range(n):
                if is_safe(row, col):
                    board[row][col] = 'Q'
                    backtrack(col + 1)
                    board[row][col] = '.'

        board = [['.' for _ in range(n)] for _ in range(n)]
        # print(board)
        results = []
        backtrack(0)
        return results

# @lc code=end

