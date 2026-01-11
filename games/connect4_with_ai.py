import numpy as np
import random
import pygame
import sys
import math
from functools import lru_cache

# Colors
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# Board dimensions
ROW_COUNT = 6
COLUMN_COUNT = 7
WINDOW_LENGTH = 4

# Players
PLAYER = 0
AI = 1
EMPTY = 0
PLAYER_PIECE = 1
AI_PIECE = 2

# Scoring constants
SCORE_WIN = 100000000
SCORE_FOUR = 100
SCORE_THREE = 5
SCORE_TWO = 2
SCORE_OPP_THREE = -4
SCORE_CENTER = 3


def create_board():
    return np.zeros((ROW_COUNT, COLUMN_COUNT), dtype=np.int8)


def drop_piece(board, row, col, piece):
    board[row][col] = piece


def is_valid_location(board, col):
    return board[ROW_COUNT - 1][col] == 0


def get_next_open_row(board, col):
    for r in range(ROW_COUNT):
        if board[r][col] == 0:
            return r
    return None


def print_board(board):
    print(np.flip(board, 0))


def winning_move(board, piece):
    """Optimized win detection."""
    # Horizontal
    for r in range(ROW_COUNT):
        for c in range(COLUMN_COUNT - 3):
            if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                return True

    # Vertical
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT - 3):
            if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                return True

    # Positive diagonal
    for r in range(ROW_COUNT - 3):
        for c in range(COLUMN_COUNT - 3):
            if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                return True

    # Negative diagonal
    for r in range(3, ROW_COUNT):
        for c in range(COLUMN_COUNT - 3):
            if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                return True

    return False


def evaluate_window(window, piece, opp_piece):
    """Evaluate a window of 4 cells. Expects tuple for caching efficiency."""
    piece_count = window.count(piece)
    empty_count = window.count(EMPTY)
    opp_count = window.count(opp_piece)

    if piece_count == 4:
        return SCORE_FOUR
    elif piece_count == 3 and empty_count == 1:
        return SCORE_THREE
    elif piece_count == 2 and empty_count == 2:
        return SCORE_TWO
    elif opp_count == 3 and empty_count == 1:
        return SCORE_OPP_THREE
    return 0


def score_position(board, piece):
    """Score the entire board position for a piece."""
    score = 0
    opp_piece = PLAYER_PIECE if piece == AI_PIECE else AI_PIECE

    # Center column bonus
    center_col = COLUMN_COUNT // 2
    center_count = np.count_nonzero(board[:, center_col] == piece)
    score += center_count * SCORE_CENTER

    # Horizontal
    for r in range(ROW_COUNT):
        row_array = board[r, :]
        for c in range(COLUMN_COUNT - 3):
            window = tuple(row_array[c:c+4])
            score += evaluate_window(window, piece, opp_piece)

    # Vertical
    for c in range(COLUMN_COUNT):
        col_array = board[:, c]
        for r in range(ROW_COUNT - 3):
            window = tuple(col_array[r:r+4])
            score += evaluate_window(window, piece, opp_piece)

    # Positive diagonal
    for r in range(ROW_COUNT - 3):
        for c in range(COLUMN_COUNT - 3):
            window = tuple(board[r+i][c+i] for i in range(4))
            score += evaluate_window(window, piece, opp_piece)

    # Negative diagonal
    for r in range(3, ROW_COUNT):
        for c in range(COLUMN_COUNT - 3):
            window = tuple(board[r-i][c+i] for i in range(4))
            score += evaluate_window(window, piece, opp_piece)

    return score


def get_valid_locations(board):
    """Get list of valid columns, prioritizing center."""
    valid = [c for c in range(COLUMN_COUNT) if board[ROW_COUNT - 1][c] == 0]
    # Sort by distance from center (center first)
    center = COLUMN_COUNT // 2
    return sorted(valid, key=lambda c: abs(c - center))


def is_terminal_node(board):
    return winning_move(board, PLAYER_PIECE) or winning_move(board, AI_PIECE) or len(get_valid_locations(board)) == 0


def minimax(board, depth, alpha, beta, maximizing_player):
    """Minimax with alpha-beta pruning - optimized."""
    valid_locations = get_valid_locations(board)
    is_terminal = is_terminal_node(board)

    if depth == 0 or is_terminal:
        if is_terminal:
            if winning_move(board, AI_PIECE):
                return None, SCORE_WIN
            elif winning_move(board, PLAYER_PIECE):
                return None, -SCORE_WIN
            else:
                return None, 0
        return None, score_position(board, AI_PIECE)

    if maximizing_player:
        value = -math.inf
        best_col = valid_locations[0]  # Default to center-most valid column

        for col in valid_locations:
            row = get_next_open_row(board, col)
            b_copy = board.copy()
            b_copy[row][col] = AI_PIECE
            new_score = minimax(b_copy, depth - 1, alpha, beta, False)[1]

            if new_score > value:
                value = new_score
                best_col = col

            alpha = max(alpha, value)
            if alpha >= beta:
                break

        return best_col, value

    else:
        value = math.inf
        best_col = valid_locations[0]

        for col in valid_locations:
            row = get_next_open_row(board, col)
            b_copy = board.copy()
            b_copy[row][col] = PLAYER_PIECE
            new_score = minimax(b_copy, depth - 1, alpha, beta, True)[1]

            if new_score < value:
                value = new_score
                best_col = col

            beta = min(beta, value)
            if alpha >= beta:
                break

        return best_col, value


def draw_board(screen, board, squaresize, radius, height):
    """Draw the game board."""
    half_sq = squaresize // 2

    for c in range(COLUMN_COUNT):
        x = c * squaresize
        for r in range(ROW_COUNT):
            y = r * squaresize + squaresize
            pygame.draw.rect(screen, BLUE, (x, y, squaresize, squaresize))
            pygame.draw.circle(screen, BLACK, (x + half_sq, y + half_sq), radius)

    for c in range(COLUMN_COUNT):
        x = c * squaresize + half_sq
        for r in range(ROW_COUNT):
            piece = board[r][c]
            if piece != 0:
                y = height - (r * squaresize + half_sq)
                color = RED if piece == PLAYER_PIECE else YELLOW
                pygame.draw.circle(screen, color, (x, y), radius)

    pygame.display.update()


def main():
    pygame.init()

    squaresize = 100
    width = COLUMN_COUNT * squaresize
    height = (ROW_COUNT + 1) * squaresize
    radius = squaresize // 2 - 5
    half_sq = squaresize // 2

    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Connect 4 vs AI")
    font = pygame.font.SysFont("monospace", 75)

    board = create_board()
    print_board(board)
    draw_board(screen, board, squaresize, radius, height)

    game_over = False
    turn = random.randint(PLAYER, AI)

    while not game_over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEMOTION and turn == PLAYER:
                pygame.draw.rect(screen, BLACK, (0, 0, width, squaresize))
                posx = event.pos[0]
                pygame.draw.circle(screen, RED, (posx, half_sq), radius)
                pygame.display.update()

            if event.type == pygame.MOUSEBUTTONDOWN and turn == PLAYER:
                pygame.draw.rect(screen, BLACK, (0, 0, width, squaresize))
                col = event.pos[0] // squaresize

                if is_valid_location(board, col):
                    row = get_next_open_row(board, col)
                    drop_piece(board, row, col, PLAYER_PIECE)

                    if winning_move(board, PLAYER_PIECE):
                        label = font.render("You win!!", True, RED)
                        screen.blit(label, (40, 10))
                        game_over = True

                    turn = AI
                    print_board(board)
                    draw_board(screen, board, squaresize, radius, height)

        # AI turn
        if turn == AI and not game_over:
            col, _ = minimax(board, 5, -math.inf, math.inf, True)

            if col is not None and is_valid_location(board, col):
                row = get_next_open_row(board, col)
                drop_piece(board, row, col, AI_PIECE)

                if winning_move(board, AI_PIECE):
                    label = font.render("AI wins!!", True, YELLOW)
                    screen.blit(label, (40, 10))
                    game_over = True

                print_board(board)
                draw_board(screen, board, squaresize, radius, height)
                turn = PLAYER

        if game_over:
            pygame.display.update()
            pygame.time.wait(3000)


if __name__ == "__main__":
    main()