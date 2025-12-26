
import random
from dataclasses import dataclass, field
from typing import List, Tuple
from enum import Enum, auto

BOARD_SIZE = 20
GROWTH_INTERVAL = 5
RED = '\033[91m'
RESET = '\033[0m'

class Direction(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()

@dataclass
class Snake:
    body: List[Tuple[int, int]] = field(init=False)
    remaining_moves: int = GROWTH_INTERVAL
    direction: Direction = field(init=False)
    
    def __post_init__(self):
        self.direction = random.choice(list(Direction))
        
        # Calculate center
        head_r, head_c = BOARD_SIZE // 2, BOARD_SIZE // 2
        
        # Determine tail direction (opposite to head direction)
        dr, dc = 0, 0
        if self.direction == Direction.UP: dr, dc = 1, 0
        elif self.direction == Direction.DOWN: dr, dc = -1, 0
        elif self.direction == Direction.LEFT: dr, dc = 0, 1
        elif self.direction == Direction.RIGHT: dr, dc = 0, -1
        
        # Generate body of length 5 (tail to head)
        self.body = []
        for i in range(4, -1, -1):
            r = head_r + (dr * i)
            c = head_c + (dc * i)
            self.body.append((r, c))
    
    @property
    def size(self):
        return len(self.body)

    @property
    def head(self):
        return self.body[-1]

    def __str__(self):
        return f"Direction:{self.direction.name}, Head:{self.head}, Remaining moves:{self.remaining_moves}, Size:{self.size}, Body:{self.body}"

    def predict_collision(self, new_head: Tuple[int, int]) -> Tuple[bool, str]:
        """Returns (is_collision, reason_message)"""
        x, y = new_head
        if new_head in self.body[1:]:
            return True, "collision with self"
        if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
            return True, "out of bounds"
        return False, ""

    def move(self, direction: Direction) -> bool:
        """
        Moves the snake. Returns True if move was successful, False if Game Over.
        """
        x, y = self.head
        new_head = None
        if direction == Direction.UP:
            new_head = (x - 1, y)
        elif direction == Direction.DOWN:
            new_head = (x + 1, y)
        elif direction == Direction.LEFT:
            new_head = (x, y - 1)
        elif direction == Direction.RIGHT:
            new_head = (x, y + 1)
            
        if new_head:
            is_over, reason = self.predict_collision(new_head)
            if is_over:
                print(f"{RED}Heading {direction.name}... Game over, {reason} at {new_head}{RESET}")
                return False
            
            self.direction = direction
            if self.remaining_moves > 1:
                self.remaining_moves -= 1
                self.body.pop(0)
            else:
                self.remaining_moves = GROWTH_INTERVAL
            self.body.append(new_head)
            return True
        return True

def main():
    snake = Snake()
    print("Initial snake state:")
    print(snake)
    
    # Map opposite directions to avoid invalid moves
    opposite_map = {
        Direction.UP: Direction.DOWN,
        Direction.DOWN: Direction.UP,
        Direction.LEFT: Direction.RIGHT,
        Direction.RIGHT: Direction.LEFT
    }
    
    for i in range(1, 21):
        # Filter out the opposite of the current direction
        forbidden = opposite_map[snake.direction]
        valid_moves = [d for d in Direction if d != forbidden]
        
        move = random.choice(valid_moves)
        
        print(f"\nMove {i}: {move.name}")
        if not snake.move(move):
            break
        print(snake)

if __name__ == "__main__":
    main()