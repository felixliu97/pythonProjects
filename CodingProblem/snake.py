import sys

class Snake:
    def __init__(self):
        self.body = [(10,5),(10,6),(10,7),(10,8),(10,9)]
        self.remaining_moves = 5
        self.direction = 'R'
        self.board_size = 20

    def print_snake(self):
        print(f"Direction:{self.direction}, Head:{self.body[-1]}, Remaining moves to grow by one:{self.remaining_moves}, Size:{len(self.body)}, Body:{self.body}")
    
    def is_game_over(self, new_head, new_direction):
        x, y = new_head
        if new_head in self.body[1:]:
            print(f"Heading {new_direction}... Game over, collision at {new_head}")
            return True
        if not (0 <= x < self.board_size and 0 <= y < self.board_size):
            print(f"Heading {new_direction}... Game over, out of bound at {new_head}")
            return True
        return False

    def move(self, direction):
        x, y = self.body[-1]
        cur_direction = self.direction
        new_head = None
        if direction == 'U' and cur_direction != 'D':
            new_head = (x - 1, y)
        elif direction == 'D' and cur_direction != 'U':
            new_head = (x + 1, y)
        elif direction == 'L' and cur_direction != 'R':
            new_head = (x, y - 1)
        elif direction == 'R' and cur_direction != 'L':
            new_head = (x, y + 1)
        if new_head:
            if self.is_game_over(new_head, direction):
                sys.exit(1)
            else:
                self.direction = direction
                if self.remaining_moves > 1:
                    self.remaining_moves -= 1
                    self.body.pop(0)
                else:
                    self.remaining_moves = 5
                self.body.append(new_head)

def main():
    snake = Snake()
    snake.print_snake()
    for _ in range(11):
        snake.move('U')
        snake.print_snake()
    # snake.move('U')
    # snake.print_snake()
    # snake.move('L')
    # snake.print_snake()
    # snake.move('D')
    # snake.print_snake()

if __name__ == "__main__":
    main()