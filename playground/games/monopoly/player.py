"""
Player module for Monopoly game.

Manages player state, money, properties, and actions.
"""

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

from .property import Property, Street, Railroad, Utility, PropertyColor
from .cards import CardType

if TYPE_CHECKING:
    from .board import Board


@dataclass
class Player:
    """
    Represents a player in the Monopoly game.
    
    Attributes:
        name: Player's display name.
        token: Token symbol (e.g., emoji or character).
        money: Current cash balance.
        position: Current board position (0-39).
        properties: List of owned properties.
        in_jail: Whether player is in jail.
        jail_turns: Number of turns spent in jail.
        jail_cards: Get Out of Jail Free cards held.
        is_bankrupt: Whether player is bankrupt.
    """
    name: str
    token: str = "🎩"
    money: int = 1500
    position: int = 0
    properties: list[Property] = field(default_factory=list)
    in_jail: bool = False
    jail_turns: int = 0
    jail_cards: list[CardType] = field(default_factory=list)
    is_bankrupt: bool = False
    
    def receive(self, amount: int) -> None:
        """Add money to player's balance."""
        self.money += amount
        print(f"  {self.name} received ${amount}. Balance: ${self.money}")
    
    def pay(self, amount: int) -> bool:
        """
        Deduct money from player's balance.
        
        Args:
            amount: Amount to pay.
            
        Returns:
            True if payment successful, False if insufficient funds.
        """
        if self.money >= amount:
            self.money -= amount
            print(f"  {self.name} paid ${amount}. Balance: ${self.money}")
            return True
        return False
    
    def pay_to(self, recipient: "Player", amount: int) -> bool:
        """
        Pay another player.
        
        Args:
            recipient: Player to receive payment.
            amount: Amount to transfer.
            
        Returns:
            True if successful.
        """
        if self.pay(amount):
            recipient.receive(amount)
            return True
        return False
    
    def move(self, spaces: int, board_size: int = 40) -> bool:
        """
        Move player by a number of spaces.
        
        Args:
            spaces: Number of spaces to move (can be negative).
            board_size: Total board spaces.
            
        Returns:
            True if player passed GO.
        """
        old_position = self.position
        self.position = (self.position + spaces) % board_size
        
        # Check if passed GO (only for forward movement)
        passed_go = spaces > 0 and self.position < old_position
        return passed_go
    
    def move_to(self, position: int, board_size: int = 40) -> bool:
        """
        Move player to a specific position.
        
        Args:
            position: Target board position.
            
        Returns:
            True if player passed GO.
        """
        old_position = self.position
        self.position = position % board_size
        
        # Check if passed GO
        passed_go = self.position < old_position and position != old_position
        return passed_go
    
    def add_property(self, prop: Property) -> None:
        """Add a property to player's portfolio."""
        prop.owner = self
        self.properties.append(prop)
    
    def remove_property(self, prop: Property) -> None:
        """Remove a property from player's portfolio."""
        prop.owner = None
        self.properties.remove(prop)
    
    def get_streets_by_color(self, color: PropertyColor) -> list[Street]:
        """Get all streets of a specific color owned by player."""
        return [p for p in self.properties 
                if isinstance(p, Street) and p.color == color]
    
    def has_monopoly(self, color: PropertyColor) -> bool:
        """Check if player owns all properties of a color group."""
        color_counts = {
            PropertyColor.BROWN: 2,
            PropertyColor.DARK_BLUE: 2,
            PropertyColor.LIGHT_BLUE: 3,
            PropertyColor.PINK: 3,
            PropertyColor.ORANGE: 3,
            PropertyColor.RED: 3,
            PropertyColor.YELLOW: 3,
            PropertyColor.GREEN: 3,
        }
        required = color_counts.get(color, 3)
        owned = len(self.get_streets_by_color(color))
        return owned >= required
    
    def count_railroads(self) -> int:
        """Count number of railroads owned."""
        return sum(1 for p in self.properties if isinstance(p, Railroad))
    
    def count_utilities(self) -> int:
        """Count number of utilities owned."""
        return sum(1 for p in self.properties if isinstance(p, Utility))
    
    def calculate_repairs(self, house_cost: int, hotel_cost: int) -> int:
        """
        Calculate repair costs for Chance/Community Chest cards.
        
        Args:
            house_cost: Cost per house.
            hotel_cost: Cost per hotel.
            
        Returns:
            Total repair cost.
        """
        total = 0
        for prop in self.properties:
            if isinstance(prop, Street):
                if prop.has_hotel:
                    total += hotel_cost
                else:
                    total += prop.houses * house_cost
        return total
    
    def add_jail_card(self, card_type: CardType) -> None:
        """Add a Get Out of Jail Free card."""
        self.jail_cards.append(card_type)
    
    def use_jail_card(self) -> Optional[CardType]:
        """
        Use a Get Out of Jail Free card.
        
        Returns:
            The card type used, or None if no cards available.
        """
        if self.jail_cards:
            return self.jail_cards.pop(0)
        return None
    
    def go_to_jail(self) -> None:
        """Send player to jail."""
        self.position = 10  # Jail position
        self.in_jail = True
        self.jail_turns = 0
        print(f"  {self.name} is now in JAIL!")
    
    def leave_jail(self) -> None:
        """Release player from jail."""
        self.in_jail = False
        self.jail_turns = 0
        print(f"  {self.name} is released from jail!")
    
    def total_assets(self) -> int:
        """
        Calculate total asset value (for bankruptcy checks).
        
        Returns:
            Total value of money + mortgageable properties + sellable houses.
        """
        total = self.money
        
        for prop in self.properties:
            if not prop.is_mortgaged:
                total += prop.mortgage_value
            if isinstance(prop, Street):
                total += prop.houses * (prop.house_cost // 2)
        
        return total
    
    def declare_bankruptcy(self, creditor: Optional["Player"] = None) -> None:
        """
        Declare bankruptcy and transfer assets.
        
        Args:
            creditor: Player to receive assets, or None for bank.
        """
        self.is_bankrupt = True
        print(f"\n{'='*40}")
        print(f"  💸 {self.name} is BANKRUPT!")
        print(f"{'='*40}")
        
        if creditor:
            # Transfer properties to creditor
            for prop in self.properties[:]:
                self.remove_property(prop)
                creditor.add_property(prop)
            creditor.receive(self.money)
        else:
            # Return properties to bank (unowned)
            for prop in self.properties[:]:
                prop.owner = None
                prop.is_mortgaged = False
                if isinstance(prop, Street):
                    prop.houses = 0
        
        self.money = 0
        self.properties.clear()
    
    def __str__(self) -> str:
        return f"{self.token} {self.name}: ${self.money} at position {self.position}"
