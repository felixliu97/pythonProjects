"""
Monopoly Game Package

A command-line implementation of the classic Monopoly board game.
"""

from .game import MonopolyGame
from .player import Player
from .board import Board
from .property import Property, Street, Railroad, Utility
from .dice import Dice
from .bank import Bank
from .gui import MonopolyGUI

__version__ = "1.0.0"
__all__ = [
    "MonopolyGame",
    "MonopolyGUI",
    "Player", 
    "Board",
    "Property",
    "Street",
    "Railroad", 
    "Utility",
    "Dice",
    "Bank",
]
