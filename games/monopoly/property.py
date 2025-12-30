"""
Property module for Monopoly game.

Contains classes for all property types: Streets, Railroads, and Utilities.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .player import Player


class PropertyColor(Enum):
    """Color groups for street properties."""
    BROWN = "Brown"
    LIGHT_BLUE = "Light Blue"
    PINK = "Pink"
    ORANGE = "Orange"
    RED = "Red"
    YELLOW = "Yellow"
    GREEN = "Green"
    DARK_BLUE = "Dark Blue"


@dataclass
class Property(ABC):
    """
    Abstract base class for all purchasable properties.
    
    Attributes:
        name: Property name.
        price: Purchase price.
        mortgage_value: Amount received when mortgaging (half of price).
        owner: Current owner of the property.
        is_mortgaged: Whether the property is mortgaged.
    """
    name: str
    price: int
    position: int
    owner: Optional["Player"] = field(default=None, repr=False)
    is_mortgaged: bool = False
    
    @property
    def mortgage_value(self) -> int:
        """Half of the purchase price."""
        return self.price // 2
    
    @property
    def unmortgage_cost(self) -> int:
        """Cost to unmortgage (110% of mortgage value)."""
        return int(self.mortgage_value * 1.1)
    
    @abstractmethod
    def calculate_rent(self, dice_roll: int = 0) -> int:
        """Calculate rent owed when another player lands here."""
        pass
    
    def mortgage(self) -> int:
        """
        Mortgage the property.
        
        Returns:
            Amount received from mortgaging.
        """
        if self.is_mortgaged:
            raise ValueError(f"{self.name} is already mortgaged")
        self.is_mortgaged = True
        return self.mortgage_value
    
    def unmortgage(self) -> int:
        """
        Unmortgage the property.
        
        Returns:
            Cost to unmortgage.
        """
        if not self.is_mortgaged:
            raise ValueError(f"{self.name} is not mortgaged")
        cost = self.unmortgage_cost
        self.is_mortgaged = False
        return cost


@dataclass
class Street(Property):
    """
    Street property with houses and hotels.
    
    Attributes:
        color: Color group this street belongs to.
        rent_levels: Rent at each level (0=base, 1-4=houses, 5=hotel).
        house_cost: Cost to build one house.
        houses: Number of houses (0-4) or 5 for hotel.
    """
    color: PropertyColor = PropertyColor.BROWN
    rent_levels: tuple = field(default_factory=lambda: (2, 10, 30, 90, 160, 250))
    house_cost: int = 50
    houses: int = 0
    
    def calculate_rent(self, dice_roll: int = 0) -> int:
        """
        Calculate rent based on houses/hotels and monopoly status.
        
        Args:
            dice_roll: Not used for streets.
            
        Returns:
            Rent amount owed.
        """
        if self.is_mortgaged:
            return 0
            
        base_rent = self.rent_levels[self.houses]
        
        # Double rent if monopoly owned and no houses
        if self.houses == 0 and self.owner and self._owner_has_monopoly():
            return base_rent * 2
            
        return base_rent
    
    def _owner_has_monopoly(self) -> bool:
        """Check if owner has all properties of this color."""
        if not self.owner:
            return False
        return self.owner.has_monopoly(self.color)
    
    def can_build(self, group_houses: list[int] = None) -> bool:
        """
        Check if a house can be built on this property.
        
        Args:
            group_houses: List of house counts for all properties in the color group.
        """
        if self.is_mortgaged or self.houses >= 5:
            return False
        if not self.owner or not self._owner_has_monopoly():
            return False
            
        # Even building rule: Cannot build if this property would have >1 more house than others
        if group_houses:
            if self.houses > min(group_houses):
                return False
                
        return True
    
    def build_house(self) -> int:
        """
        Build a house on this property.
        
        Returns:
            Cost of building.
            
        Raises:
            ValueError: If building is not allowed.
        """
        if not self.can_build():
            raise ValueError(f"Cannot build on {self.name}")
        self.houses += 1
        return self.house_cost
    
    def sell_house(self) -> int:
        """
        Sell a house from this property.
        
        Returns:
            Amount received (half of house cost).
        """
        if self.houses <= 0:
            raise ValueError(f"No houses to sell on {self.name}")
        self.houses -= 1
        return self.house_cost // 2
    
    @property
    def has_hotel(self) -> bool:
        """Check if property has a hotel."""
        return self.houses == 5


@dataclass  
class Railroad(Property):
    """
    Railroad property. Rent scales with number owned.
    
    Base rent is $25, doubling for each additional railroad owned.
    """
    
    def calculate_rent(self, dice_roll: int = 0) -> int:
        """
        Calculate rent based on number of railroads owned.
        
        Returns:
            Rent: $25, $50, $100, or $200.
        """
        if self.is_mortgaged or not self.owner:
            return 0
            
        railroads_owned = self.owner.count_railroads()
        return 25 * (2 ** (railroads_owned - 1))


@dataclass
class Utility(Property):
    """
    Utility property (Electric Company, Water Works).
    
    Rent is based on dice roll:
    - 1 utility owned: 4x dice roll
    - 2 utilities owned: 10x dice roll
    """
    
    def calculate_rent(self, dice_roll: int = 0) -> int:
        """
        Calculate rent based on dice roll and utilities owned.
        
        Args:
            dice_roll: Sum of dice that brought player here.
            
        Returns:
            Rent amount (4x or 10x dice roll).
        """
        if self.is_mortgaged or not self.owner:
            return 0
            
        utilities_owned = self.owner.count_utilities()
        multiplier = 10 if utilities_owned == 2 else 4
        return multiplier * dice_roll
