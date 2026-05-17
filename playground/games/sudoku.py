# GUI.py
import pygame
import time
import sudoku_generator as gen

pygame.font.init()


class Grid:
    # board = [[7, 8, 0, 4, 0, 0, 1, 2, 0], [6, 0, 0, 0, 7, 5, 0, 0, 9],
    #          [0, 0, 0, 6, 0, 1, 0, 7, 8], [0, 0, 7, 0, 4, 0, 2, 6, 0],
    #          [0, 0, 1, 0, 5, 0, 9, 3, 0], [9, 0, 4, 0, 6, 0, 0, 0, 5],
    #          [0, 7, 0, 3, 0, 0, 0, 1, 2], [1, 2, 0, 0, 0, 7, 4, 0, 0],
    #          [0, 4, 9, 2, 0, 6, 0, 0, 7]]
    
    board = [[5, 0, 0, 0, 1, 0, 7, 0, 9], [1, 0, 0, 4, 7, 0, 0, 5, 0],
            [9, 0, 2, 3, 0, 0, 4, 1, 8], [6, 0, 0, 0, 0, 0, 8, 7, 4],
            [0, 8, 7, 5, 0, 4, 9, 2, 0], [4, 2, 1, 0, 0, 0, 0, 0, 3],
            [7, 9, 5, 0, 0, 1, 3, 0, 2], [0, 1, 0, 0, 9, 5, 0, 0, 7],
            [8, 0, 6, 0, 3, 0, 0, 0, 5]]

    # board = [[4, 3, 5, 2, 6, 9, 7, 8, 1], [6, 8, 2, 5, 7, 1, 4, 9, 3],
    #          [1, 9, 7, 8, 3, 4, 5, 6, 2], [8, 2, 6, 1, 9, 5, 3, 4, 7],
    #          [3, 7, 4, 6, 8, 2, 9, 1, 5], [9, 5, 1, 7, 4, 3, 6, 2, 8],
    #          [5, 1, 9, 3, 2, 6, 8, 7, 4], [2, 4, 8, 9, 5, 7, 1, 3, 6],
    #          [7, 6, 3, 4, 1, 8, 2, 5, 0]]

    # board = gen.main('Easy')

    def __init__(self, rows, cols, width, height, win):
        self.rows = rows
        self.cols = cols
        self.cubes = [[
            Cube(self.board[i][j], i, j, width, height) for j in range(cols)
        ] for i in range(rows)]
        self.width = width
        self.height = height
        self.model = None
        self.update_model()
        self.selected = None
        self.selectedValue = None
        self.win = win

    def update_model(self):
        self.model = [[(self.cubes[i][j].value if not self.cubes[i][j].is_wrong else 0) for j in range(self.cols)]
                      for i in range(self.rows)]

    def place(self, val):
        row, col = self.selected
        if not self.cubes[row][col].is_original:
            self.cubes[row][col].set(val)
            self.cubes[row][col].set_temp(0)
            self.cubes[row][col].is_wrong = False
            self.update_model()

            if valid(self.model, val, (row, col)) and self.solve():
                self.cubes[row][col].is_wrong = False
                self.update_model()
                return True
            else:
                self.cubes[row][col].is_wrong = True
                self.update_model()
                return False
        return False

    def sketch(self, val):
        row, col = self.selected
        self.cubes[row][col].set_temp(val)
        self.cubes[row][col].is_wrong = False

    def draw(self):
        # 1. Draw all cube backgrounds first
        for i in range(self.rows):
            for j in range(self.cols):
                self.cubes[i][j].draw_background(self.win)

        # 2. Draw Grid Lines on top of backgrounds
        gap = self.width / 9
        for i in range(self.rows + 1):
            if i % 3 == 0 and i != 0:
                thick = 4
                color = (30, 41, 59)  # Slate-800 for major box boundaries
            else:
                thick = 1
                color = (148, 163, 184)  # Slate-400 for minor lines
            pygame.draw.line(self.win, color, (0, i * gap),
                             (self.width, i * gap), thick)
            pygame.draw.line(self.win, color, (i * gap, 0),
                             (i * gap, self.height), thick)

        # 3. Draw Cube texts and borders on top
        for i in range(self.rows):
            for j in range(self.cols):
                self.cubes[i][j].draw_text_and_border(self.win)

    def select(self, row, col):
        # Reset all other selection states
        for i in range(self.rows):
            for j in range(self.cols):
                self.cubes[i][j].selected = False

        self.cubes[row][col].selected = True
        self.selected = (row, col)
        self.update_highlights()

    def update_highlights(self):
        if not self.selected:
            self.selectedValue = 0
        else:
            row, col = self.selected
            val = self.cubes[row][col].value
            temp = self.cubes[row][col].temp
            self.selectedValue = val if val != 0 else temp

        highlighted_count = 0
        for i in range(self.rows):
            for j in range(self.cols):
                self.cubes[i][j].highlighted = False
                if self.selectedValue != 0:
                    cell_val = self.cubes[i][j].value
                    cell_temp = self.cubes[i][j].temp
                    # A cell is highlighted if its displayed number matches self.selectedValue
                    compare_val = cell_val if cell_val != 0 else cell_temp
                    if compare_val == self.selectedValue:
                        self.cubes[i][j].highlighted = True
                        highlighted_count += 1
        print(f"Selected value: {self.selectedValue}, Total highlighted cells: {highlighted_count}")


    def clear(self):
        row, col = self.selected
        if self.cubes[row][col].value == 0:
            self.cubes[row][col].set_temp(0)
            self.cubes[row][col].is_wrong = False

    def click(self, pos):
        """
        :param: pos
        :return: (row, col)
        """
        if pos[0] < self.width and pos[1] < self.height:
            gap = self.width / 9
            x = pos[0] // gap
            y = pos[1] // gap
            return (int(y), int(x))
        else:
            return None

    def is_finished(self):
        for i in range(self.rows):
            for j in range(self.cols):
                if self.cubes[i][j].value == 0 or self.cubes[i][j].is_wrong:
                    return False
        return True

    def solve(self):
        find = find_empty(self.model)
        if not find:
            return True
        else:
            row, col = find

        for i in range(1, 10):
            if valid(self.model, i, (row, col)):
                self.model[row][col] = i

                if self.solve():
                    return True

                self.model[row][col] = 0

        return False

    def solve_gui(self):
        self.update_model()
        find = find_empty(self.model)
        if not find:
            return True
        else:
            row, col = find

        for i in range(1, 10):
            if valid(self.model, i, (row, col)):
                self.model[row][col] = i
                self.cubes[row][col].set(i)
                self.cubes[row][col].draw_change(self.win, True)
                self.update_model()
                pygame.display.update()
                pygame.time.delay(100)

                if self.solve_gui():
                    return True

                self.model[row][col] = 0
                self.cubes[row][col].set(0)
                self.update_model()
                self.cubes[row][col].draw_change(self.win, False)
                pygame.display.update()
                pygame.time.delay(100)

        return False


class Cube:
    rows = 9
    cols = 9

    def __init__(self, value, row, col, width, height):
        self.value = value
        self.temp = 0
        self.row = row
        self.col = col
        self.width = width
        self.height = height
        self.selected = False
        self.highlighted = False
        self.is_original = (value != 0)
        self.is_wrong = False

    def draw_background(self, win):
        gap = self.width / 9
        x = self.col * gap
        y = self.row * gap

        # Fill background based on selection/highlight state
        if self.selected:
            pygame.draw.rect(win, (186, 230, 253), (x, y, gap, gap), 0)  # Sleek modern light blue
        elif self.highlighted:
            pygame.draw.rect(win, (254, 240, 138), (x, y, gap, gap), 0)  # Crisp soft yellow
        else:
            pygame.draw.rect(win, (255, 255, 255), (x, y, gap, gap), 0)  # White

    def draw_text_and_border(self, win):
        gap = self.width / 9
        x = self.col * gap
        y = self.row * gap

        # Draw borders for selection/highlight to give high-contrast definition
        if self.selected:
            pygame.draw.rect(win, (14, 165, 233), (x, y, gap, gap), 3)  # Bright blue border
        elif self.highlighted:
            pygame.draw.rect(win, (234, 179, 8), (x, y, gap, gap), 2)   # Soft amber border

        # Draw text
        try:
            fnt = pygame.font.SysFont("Inter", 38)
        except Exception:
            fnt = pygame.font.SysFont("comicsans", 40)

        if self.value != 0:
            if self.is_original:
                text = fnt.render(str(self.value), 1, (0, 0, 0))  # Original (black)
            elif self.is_wrong:
                text = fnt.render(str(self.value), 1, (220, 38, 38))  # Wrong user number (deep red)
            else:
                text = fnt.render(str(self.value), 1, (30, 58, 138))  # Correct user number (navy-blue)
            win.blit(text, (x + (gap / 2 - text.get_width() / 2), y +
                            (gap / 2 - text.get_height() / 2)))
        elif self.temp != 0:
            if self.is_wrong:
                text = fnt.render(str(self.temp), 1, (220, 38, 38))
            else:
                text = fnt.render(str(self.temp), 1, (100, 116, 139))
            win.blit(text, (x + (gap / 2 - text.get_width() / 2), y +
                            (gap / 2 - text.get_height() / 2)))

    def draw_change(self, win, g=True):
        try:
            fnt = pygame.font.SysFont("Inter", 38)
        except Exception:
            fnt = pygame.font.SysFont("comicsans", 40)

        gap = self.width / 9
        x = self.col * gap
        y = self.row * gap

        pygame.draw.rect(win, (255, 255, 255), (x, y, gap, gap), 0)

        text = fnt.render(str(self.value), 1, (15, 23, 42))
        win.blit(text, (x + (gap / 2 - text.get_width() / 2), y +
                        (gap / 2 - text.get_height() / 2)))
        if g:
            pygame.draw.rect(win, (34, 197, 94), (x, y, gap, gap), 3)  # Green for success
        else:
            pygame.draw.rect(win, (239, 68, 68), (x, y, gap, gap), 3)  # Red for backtrack

    def set(self, val):
        self.value = val

    def set_temp(self, val):
        self.temp = val


def find_empty(bo):
    for i in range(len(bo)):
        for j in range(len(bo[0])):
            if bo[i][j] == 0:
                return (i, j)  # row, col

    return None


def valid(bo, num, pos):
    # Check row
    for i in range(len(bo[0])):
        if bo[pos[0]][i] == num and pos[1] != i:
            return False

    # Check column
    for i in range(len(bo)):
        if bo[i][pos[1]] == num and pos[0] != i:
            return False

    # Check box
    box_x = pos[1] // 3
    box_y = pos[0] // 3

    for i in range(box_y * 3, box_y * 3 + 3):
        for j in range(box_x * 3, box_x * 3 + 3):
            if bo[i][j] == num and (i, j) != pos:
                return False

    return True


def redraw_window(win, board, time, strikes, feedback_msg=None):
    win.fill((255, 255, 255))
    
    # 1. Draw grid and board first
    board.draw()

    # 2. Draw bottom panel background
    pygame.draw.rect(win, (248, 250, 252), (0, 540, 540, 60))
    # Draw top border line to separate panel from board
    pygame.draw.line(win, (226, 232, 240), (0, 540), (540, 540), 2)

    # Use a nice modern font
    try:
        fnt = pygame.font.SysFont("Inter", 28)
    except Exception:
        fnt = pygame.font.SysFont("comicsans", 30)

    # 3. Draw time (right-aligned, perfectly centered vertically)
    time_str = "Time: " + format_time(time)
    time_text = fnt.render(time_str, 1, (15, 23, 42))
    win.blit(time_text, (540 - 20 - time_text.get_width(), 570 - time_text.get_height() // 2))

    # 4. Draw Strikes (left-aligned, perfectly centered vertically)
    if strikes > 0:
        strikes_text = fnt.render("X " * strikes, 1, (239, 68, 68))
        win.blit(strikes_text, (20, 570 - strikes_text.get_height() // 2))

    # 5. Draw success or feedback message
    if board.is_finished():
        success_text = fnt.render("Success!", 1, (34, 197, 94))
        win.blit(success_text, (540 // 2 - success_text.get_width() // 2, 570 - success_text.get_height() // 2))
    elif feedback_msg:
        msg_text, msg_color = feedback_msg
        fb_text = fnt.render(msg_text, 1, msg_color)
        win.blit(fb_text, (540 // 2 - fb_text.get_width() // 2, 570 - fb_text.get_height() // 2))


def format_time(secs):
    sec = secs % 60
    minute = (secs // 60) % 60
    hour = secs // 3600

    if hour > 0:
        return f"{hour}:{minute:02d}:{sec:02d}"
    else:
        return f"{minute:02d}:{sec:02d}"


def main():
    win = pygame.display.set_mode((540, 600))
    pygame.display.set_caption("Sudoku")
    board = Grid(9, 9, 540, 540, win)
    key = None
    run = True
    start_time = time.time()
    finish_time = None
    strikes = 0
    feedback_msg = None

    while run:
        if not board.is_finished():
            play_time = round(time.time() - start_time)
        else:
            if finish_time is None:
                finish_time = time.time()
            play_time = round(finish_time - start_time)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                feedback_msg = None
                
                # Determine digit value
                val = None
                if event.key == pygame.K_1 or event.key == pygame.K_KP1: val = 1
                elif event.key == pygame.K_2 or event.key == pygame.K_KP2: val = 2
                elif event.key == pygame.K_3 or event.key == pygame.K_KP3: val = 3
                elif event.key == pygame.K_4 or event.key == pygame.K_KP4: val = 4
                elif event.key == pygame.K_5 or event.key == pygame.K_KP5: val = 5
                elif event.key == pygame.K_6 or event.key == pygame.K_KP6: val = 6
                elif event.key == pygame.K_7 or event.key == pygame.K_KP7: val = 7
                elif event.key == pygame.K_8 or event.key == pygame.K_KP8: val = 8
                elif event.key == pygame.K_9 or event.key == pygame.K_KP9: val = 9
                
                if val is not None:
                    if board.selected:
                        if board.place(val):
                            print("Success")
                            feedback_msg = ("Correct!", (34, 197, 94))
                        else:
                            print("Wrong")
                            strikes += 1
                            feedback_msg = ("Incorrect!", (239, 68, 68))
                        board.update_highlights()

                        if board.is_finished():
                            finish_time = time.time()
                            print("You win")
                            feedback_msg = ("Success!", (34, 197, 94))
                            
                elif event.key == pygame.K_DELETE:
                    board.clear()
                    board.update_highlights()

                elif event.key == pygame.K_SPACE:
                    board.solve_gui()

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                clicked = board.click(pos)
                if clicked:
                    board.select(clicked[0], clicked[1])
                    feedback_msg = None

        redraw_window(win, board, play_time, strikes, feedback_msg)
        pygame.display.update()


main()
pygame.quit()