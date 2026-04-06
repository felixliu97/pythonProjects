import numpy as np
import pygame
import sys

# Colors
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# Board dimensions
ROW_COUNT = 6
COLUMN_COUNT = 7

# Player pieces
PLAYER_1 = 1
PLAYER_2 = 2


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
    """Optimized win detection using numpy slicing."""
    # Check horizontal
    for r in range(ROW_COUNT):
        for c in range(COLUMN_COUNT - 3):
            if np.all(board[r, c:c+4] == piece):
                return True

    # Check vertical
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT - 3):
            if np.all(board[r:r+4, c] == piece):
                return True

    # Check positive diagonal
    for r in range(ROW_COUNT - 3):
        for c in range(COLUMN_COUNT - 3):
            if all(board[r+i][c+i] == piece for i in range(4)):
                return True

    # Check negative diagonal
    for r in range(3, ROW_COUNT):
        for c in range(COLUMN_COUNT - 3):
            if all(board[r-i][c+i] == piece for i in range(4)):
                return True

    return False


def draw_board(screen, board, squaresize, radius, height):
    """Draw the game board - optimized to reduce redundant calculations."""
    half_square = squaresize // 2
    
    # Draw blue board with black holes
    for c in range(COLUMN_COUNT):
        x = c * squaresize
        for r in range(ROW_COUNT):
            y = r * squaresize + squaresize
            pygame.draw.rect(screen, BLUE, (x, y, squaresize, squaresize))
            pygame.draw.circle(screen, BLACK, (x + half_square, y + half_square), radius)

    # Draw pieces
    for c in range(COLUMN_COUNT):
        x = c * squaresize + half_square
        for r in range(ROW_COUNT):
            piece = board[r][c]
            if piece != 0:
                y = height - (r * squaresize + half_square)
                color = RED if piece == PLAYER_1 else YELLOW
                pygame.draw.circle(screen, color, (x, y), radius)

    pygame.display.update()


def handle_turn(board, col, piece, screen, font, squaresize, radius, height, width):
    """Handle a player's turn. Returns True if game is won."""
    if not is_valid_location(board, col):
        return False

    row = get_next_open_row(board, col)
    drop_piece(board, row, col, piece)
    print_board(board)
    draw_board(screen, board, squaresize, radius, height)

    if winning_move(board, piece):
        pygame.draw.rect(screen, BLACK, (0, 0, width, squaresize))
        color = RED if piece == PLAYER_1 else YELLOW
        label = font.render(f"Player {piece} wins!!", True, color)
        screen.blit(label, (40, 10))
        pygame.display.update()
        return True

    return False


def main():
    pygame.init()

    squaresize = 100
    width = COLUMN_COUNT * squaresize
    height = (ROW_COUNT + 1) * squaresize
    radius = squaresize // 2 - 5

    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Connect 4")
    font = pygame.font.SysFont("monospace", 75)

    board = create_board()
    print_board(board)
    draw_board(screen, board, squaresize, radius, height)

    game_over = False
    turn = 0
    half_square = squaresize // 2

    while not game_over:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEMOTION:
                pygame.draw.rect(screen, BLACK, (0, 0, width, squaresize))
                posx = event.pos[0]
                color = RED if turn == 0 else YELLOW
                pygame.draw.circle(screen, color, (posx, half_square), radius)
                pygame.display.update()

            if event.type == pygame.MOUSEBUTTONDOWN:
                pygame.draw.rect(screen, BLACK, (0, 0, width, squaresize))
                col = event.pos[0] // squaresize
                piece = PLAYER_1 if turn == 0 else PLAYER_2

                if is_valid_location(board, col):
                    game_over = handle_turn(
                        board, col, piece, screen, font,
                        squaresize, radius, height, width
                    )
                    turn = 1 - turn  # Toggle between 0 and 1

                    if game_over:
                        pygame.time.wait(3000)


if __name__ == "__main__":
    main()