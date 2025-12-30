"""
Dice module for Monopoly game.

Handles dice rolling mechanics including doubles detection.
"""

import random
from dataclasses import dataclass


@dataclass
class DiceRoll:
    """Represents the result of rolling two dice."""
    die1: int
    die2: int
    
    @property
    def total(self) -> int:
        """Sum of both dice."""
        return self.die1 + self.die2
    
    @property
    def is_doubles(self) -> bool:
        """Check if both dice show the same value."""
        return self.die1 == self.die2
    
    def __str__(self) -> str:
        doubles_str = " (DOUBLES!)" if self.is_doubles else ""
        return f"Rolled {self.die1} + {self.die2} = {self.total}{doubles_str}"


class Dice:
    """
    Handles dice rolling for the Monopoly game.
    
    Attributes:
        consecutive_doubles: Count of consecutive doubles rolled.
    """
    
    def __init__(self):
        self.consecutive_doubles: int = 0
    
    def roll(self) -> DiceRoll:
        """
        Roll two six-sided dice.
        
        Returns:
            DiceRoll containing the result.
        """
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        result = DiceRoll(die1, die2)
        
        if result.is_doubles:
            self.consecutive_doubles += 1
        else:
            self.consecutive_doubles = 0
            
        return result
    
    def reset_doubles(self) -> None:
        """Reset the consecutive doubles counter."""
        self.consecutive_doubles = 0
    
    @property
    def should_go_to_jail(self) -> bool:
        """Check if player rolled 3 consecutive doubles."""
        return self.consecutive_doubles >= 3
