"""
Bank module for Monopoly game.

Manages the bank's money, houses, hotels, and property auctions.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .property import Property, Street


@dataclass
class Bank:
    """
    The Monopoly Bank.
    
    Manages:
    - House and hotel supply (32 houses, 12 hotels)
    - Property sales and mortgages
    - Money distribution
    
    Note: The bank never runs out of money in standard Monopoly.
    """
    houses_available: int = 32
    hotels_available: int = 12
    
    def sell_house(self) -> bool:
        """
        Sell a house from the bank.
        
        Returns:
            True if house was available, False otherwise.
        """
        if self.houses_available > 0:
            self.houses_available -= 1
            return True
        print("  ⚠️ No houses available in the bank!")
        return False
    
    def return_house(self, count: int = 1) -> None:
        """Return houses to the bank."""
        self.houses_available += count
    
    def sell_hotel(self) -> bool:
        """
        Sell a hotel from the bank.
        
        Returns:
            True if hotel was available, False otherwise.
        """
        if self.hotels_available > 0:
            self.hotels_available -= 1
            # Return the 4 houses that were upgraded
            self.houses_available += 4
            return True
        print("  ⚠️ No hotels available in the bank!")
        return False
    
    def return_hotel(self, count: int = 1) -> None:
        """Return hotels to the bank."""
        self.hotels_available += count
    
    def can_build_house(self) -> bool:
        """Check if a house can be built."""
        return self.houses_available > 0
    
    def can_build_hotel(self) -> bool:
        """Check if a hotel can be built."""
        return self.hotels_available > 0
    
    def __str__(self) -> str:
        return f"Bank: {self.houses_available} houses, {self.hotels_available} hotels"
