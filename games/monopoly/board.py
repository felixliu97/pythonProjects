"""
Board module for Monopoly game.

Defines the complete 40-space Monopoly board with all properties and spaces.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union

from .property import Property, Street, Railroad, Utility, PropertyColor


class SpaceType(Enum):
    """Types of non-property board spaces."""
    GO = "GO"
    JAIL = "Jail"
    FREE_PARKING = "Free Parking"
    GO_TO_JAIL = "Go To Jail"
    CHANCE = "Chance"
    COMMUNITY_CHEST = "Community Chest"
    INCOME_TAX = "Income Tax"
    LUXURY_TAX = "Luxury Tax"


@dataclass
class SpecialSpace:
    """Represents a non-property space on the board."""
    name: str
    space_type: SpaceType
    position: int
    
    def __str__(self) -> str:
        return self.name


# Type alias for any board space
BoardSpace = Union[Property, SpecialSpace]


class Board:
    """
    Represents the Monopoly game board.
    
    Contains all 40 spaces including properties and special spaces.
    """
    
    def __init__(self):
        self.spaces: list[BoardSpace] = []
        self._initialize_board()
    
    def _initialize_board(self) -> None:
        """Create all 40 board spaces in order."""
        self.spaces = [
            # Row 1: GO to Jail
            SpecialSpace("GO", SpaceType.GO, 0),
            Street("Mediterranean Avenue", 60, 1, color=PropertyColor.BROWN,
                   rent_levels=(2, 10, 30, 90, 160, 250), house_cost=50),
            SpecialSpace("Community Chest", SpaceType.COMMUNITY_CHEST, 2),
            Street("Baltic Avenue", 60, 3, color=PropertyColor.BROWN,
                   rent_levels=(4, 20, 60, 180, 320, 450), house_cost=50),
            SpecialSpace("Income Tax", SpaceType.INCOME_TAX, 4),
            Railroad("Reading Railroad", 200, 5),
            Street("Oriental Avenue", 100, 6, color=PropertyColor.LIGHT_BLUE,
                   rent_levels=(6, 30, 90, 270, 400, 550), house_cost=50),
            SpecialSpace("Chance", SpaceType.CHANCE, 7),
            Street("Vermont Avenue", 100, 8, color=PropertyColor.LIGHT_BLUE,
                   rent_levels=(6, 30, 90, 270, 400, 550), house_cost=50),
            Street("Connecticut Avenue", 120, 9, color=PropertyColor.LIGHT_BLUE,
                   rent_levels=(8, 40, 100, 300, 450, 600), house_cost=50),
            
            # Row 2: Jail to Free Parking
            SpecialSpace("Jail / Just Visiting", SpaceType.JAIL, 10),
            Street("St. Charles Place", 140, 11, color=PropertyColor.PINK,
                   rent_levels=(10, 50, 150, 450, 625, 750), house_cost=100),
            Utility("Electric Company", 150, 12),
            Street("States Avenue", 140, 13, color=PropertyColor.PINK,
                   rent_levels=(10, 50, 150, 450, 625, 750), house_cost=100),
            Street("Virginia Avenue", 160, 14, color=PropertyColor.PINK,
                   rent_levels=(12, 60, 180, 500, 700, 900), house_cost=100),
            Railroad("Pennsylvania Railroad", 200, 15),
            Street("St. James Place", 180, 16, color=PropertyColor.ORANGE,
                   rent_levels=(14, 70, 200, 550, 750, 950), house_cost=100),
            SpecialSpace("Community Chest", SpaceType.COMMUNITY_CHEST, 17),
            Street("Tennessee Avenue", 180, 18, color=PropertyColor.ORANGE,
                   rent_levels=(14, 70, 200, 550, 750, 950), house_cost=100),
            Street("New York Avenue", 200, 19, color=PropertyColor.ORANGE,
                   rent_levels=(16, 80, 220, 600, 800, 1000), house_cost=100),
            
            # Row 3: Free Parking to Go To Jail
            SpecialSpace("Free Parking", SpaceType.FREE_PARKING, 20),
            Street("Kentucky Avenue", 220, 21, color=PropertyColor.RED,
                   rent_levels=(18, 90, 250, 700, 875, 1050), house_cost=150),
            SpecialSpace("Chance", SpaceType.CHANCE, 22),
            Street("Indiana Avenue", 220, 23, color=PropertyColor.RED,
                   rent_levels=(18, 90, 250, 700, 875, 1050), house_cost=150),
            Street("Illinois Avenue", 240, 24, color=PropertyColor.RED,
                   rent_levels=(20, 100, 300, 750, 925, 1100), house_cost=150),
            Railroad("B. & O. Railroad", 200, 25),
            Street("Atlantic Avenue", 260, 26, color=PropertyColor.YELLOW,
                   rent_levels=(22, 110, 330, 800, 975, 1150), house_cost=150),
            Street("Ventnor Avenue", 260, 27, color=PropertyColor.YELLOW,
                   rent_levels=(22, 110, 330, 800, 975, 1150), house_cost=150),
            Utility("Water Works", 150, 28),
            Street("Marvin Gardens", 280, 29, color=PropertyColor.YELLOW,
                   rent_levels=(24, 120, 360, 850, 1025, 1200), house_cost=150),
            
            # Row 4: Go To Jail to GO
            SpecialSpace("Go To Jail", SpaceType.GO_TO_JAIL, 30),
            Street("Pacific Avenue", 300, 31, color=PropertyColor.GREEN,
                   rent_levels=(26, 130, 390, 900, 1100, 1275), house_cost=200),
            Street("North Carolina Avenue", 300, 32, color=PropertyColor.GREEN,
                   rent_levels=(26, 130, 390, 900, 1100, 1275), house_cost=200),
            SpecialSpace("Community Chest", SpaceType.COMMUNITY_CHEST, 33),
            Street("Pennsylvania Avenue", 320, 34, color=PropertyColor.GREEN,
                   rent_levels=(28, 150, 450, 1000, 1200, 1400), house_cost=200),
            Railroad("Short Line", 200, 35),
            SpecialSpace("Chance", SpaceType.CHANCE, 36),
            Street("Park Place", 350, 37, color=PropertyColor.DARK_BLUE,
                   rent_levels=(35, 175, 500, 1100, 1300, 1500), house_cost=200),
            SpecialSpace("Luxury Tax", SpaceType.LUXURY_TAX, 38),
            Street("Boardwalk", 400, 39, color=PropertyColor.DARK_BLUE,
                   rent_levels=(50, 200, 600, 1400, 1700, 2000), house_cost=200),
        ]
    
    def get_space(self, position: int) -> BoardSpace:
        """Get the space at a given position."""
        return self.spaces[position % 40]
    
    def get_property(self, position: int) -> Optional[Property]:
        """Get the property at a position, or None if not a property."""
        space = self.get_space(position)
        if isinstance(space, Property):
            return space
        return None
    
    def get_all_properties(self) -> list[Property]:
        """Get all purchasable properties on the board."""
        return [s for s in self.spaces if isinstance(s, Property)]
    
    def get_railroads(self) -> list[Railroad]:
        """Get all railroad properties."""
        return [s for s in self.spaces if isinstance(s, Railroad)]
    
    def get_utilities(self) -> list[Utility]:
        """Get all utility properties."""
        return [s for s in self.spaces if isinstance(s, Utility)]
    
    def get_streets_by_color(self, color: PropertyColor) -> list[Street]:
        """Get all streets of a specific color."""
        return [s for s in self.spaces 
                if isinstance(s, Street) and s.color == color]
    
    def find_nearest_utility(self, from_position: int) -> int:
        """Find position of nearest utility from a given position."""
        utility_positions = [12, 28]  # Electric Company, Water Works
        for pos in range(from_position + 1, from_position + 41):
            actual_pos = pos % 40
            if actual_pos in utility_positions:
                return actual_pos
        return utility_positions[0]
    
    def find_nearest_railroad(self, from_position: int) -> int:
        """Find position of nearest railroad from a given position."""
        railroad_positions = [5, 15, 25, 35]
        for pos in range(from_position + 1, from_position + 41):
            actual_pos = pos % 40
            if actual_pos in railroad_positions:
                return actual_pos
        return railroad_positions[0]
    
    def display(self) -> str:
        """Generate ASCII representation of the board."""
        lines = []
        lines.append("=" * 60)
        lines.append("MONOPOLY BOARD")
        lines.append("=" * 60)
        
        for i, space in enumerate(self.spaces):
            owner_str = ""
            if isinstance(space, Property) and space.owner:
                owner_str = f" [{space.owner.name}]"
            lines.append(f"{i:2d}. {space.name}{owner_str}")
        
        return "\n".join(lines)
