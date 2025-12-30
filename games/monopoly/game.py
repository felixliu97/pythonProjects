"""
Game module for Monopoly.

Contains the main game loop and orchestration logic.
"""

from dataclasses import dataclass, field
from typing import Optional

from .board import Board, SpecialSpace, SpaceType
from .player import Player
from .property import Property, Street, Railroad, Utility
from .dice import Dice, DiceRoll
from .bank import Bank
from .cards import CardDeck, CardType


@dataclass
class MonopolyGame:
    """
    Main Monopoly game controller.
    
    Orchestrates the game flow including:
    - Turn management
    - Player movement
    - Property transactions
    - Card draws
    - Jail mechanics
    - Win condition checking
    """
    players: list[Player] = field(default_factory=list)
    board: Board = field(default_factory=Board)
    bank: Bank = field(default_factory=Bank)
    dice: Dice = field(default_factory=Dice)
    chance_deck: CardDeck = field(default_factory=lambda: CardDeck(CardType.CHANCE))
    community_chest_deck: CardDeck = field(default_factory=lambda: CardDeck(CardType.COMMUNITY_CHEST))
    current_player_index: int = 0
    turn_count: int = 0
    last_dice_roll: Optional[DiceRoll] = None
    game_over: bool = False
    winner: Optional[Player] = None
    
    def add_player(self, name: str, token: str = "🎩") -> Player:
        """
        Add a player to the game.
        
        Args:
            name: Player's display name.
            token: Token symbol.
            
        Returns:
            The created Player object.
        """
        if len(self.players) >= 4:
            raise ValueError("Maximum 4 players allowed")
        
        player = Player(name=name, token=token)
        self.players.append(player)
        return player
    
    @property
    def current_player(self) -> Player:
        """Get the current player."""
        return self.players[self.current_player_index]
    
    @property
    def active_players(self) -> list[Player]:
        """Get all non-bankrupt players."""
        return [p for p in self.players if not p.is_bankrupt]
    
    def next_turn(self) -> None:
        """Advance to the next player's turn."""
        self.dice.reset_doubles()
        
        # Find next non-bankrupt player
        for _ in range(len(self.players)):
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            if not self.current_player.is_bankrupt:
                break
        
        self.turn_count += 1
    
    def play_turn(self) -> bool:
        """
        Execute a single turn for the current player.
        
        Returns:
            True if player gets another turn (doubles), False otherwise.
        """
        player = self.current_player
        
        print(f"\n{'='*50}")
        print(f"  {player.token} {player.name}'s Turn (${player.money})")
        print(f"{'='*50}")
        
        # Handle jail
        if player.in_jail:
            if not self._handle_jail_turn(player):
                return False
        
        # Roll dice
        roll = self.dice.roll()
        self.last_dice_roll = roll
        print(f"\n  🎲 {roll}")
        
        # Check for 3 doubles = jail
        if self.dice.should_go_to_jail:
            print("  Three doubles in a row!")
            self.send_to_jail(player)
            return False
        
        # Move player
        passed_go = player.move(roll.total)
        if passed_go:
            player.receive(200)
            print("  🎉 Passed GO! Collected $200")
        
        # Handle landing space
        self._handle_space(player, roll)
        
        # Check bankruptcy
        if player.is_bankrupt:
            self._check_winner()
            return False
        
        # Doubles = roll again (unless sent to jail)
        return roll.is_doubles and not player.in_jail
    
    def _handle_jail_turn(self, player: Player) -> bool:
        """
        Handle a turn when player is in jail.
        
        Returns:
            True if player escaped jail, False to end turn.
        """
        player.jail_turns += 1
        print(f"\n  {player.name} is in jail (turn {player.jail_turns}/3)")
        
        # Options: pay, use card, or try to roll doubles
        if player.jail_cards:
            print("  Using Get Out of Jail Free card!")
            card_type = player.use_jail_card()
            if card_type == CardType.CHANCE:
                self.chance_deck.return_card(None)  # Return to deck
            else:
                self.community_chest_deck.return_card(None)
            player.leave_jail()
            return True
        
        # Try to roll doubles
        roll = self.dice.roll()
        self.last_dice_roll = roll
        print(f"  🎲 Attempting doubles: {roll}")
        
        if roll.is_doubles:
            print("  Rolled doubles! Released from jail.")
            player.leave_jail()
            player.move(roll.total)
            self._handle_space(player, roll)
            return False  # Don't roll again after escaping
        
        if player.jail_turns >= 3:
            print("  Third failed attempt. Must pay $50.")
            if player.pay(50):
                player.leave_jail()
                player.move(roll.total)
                self._handle_space(player, roll)
            else:
                self._handle_bankruptcy(player, None, 50)
        
        return False
    
    def _handle_space(self, player: Player, roll: DiceRoll) -> None:
        """Handle the effects of landing on a space."""
        space = self.board.get_space(player.position)
        print(f"\n  📍 Landed on: {space.name}")
        
        if isinstance(space, Property):
            self._handle_property(player, space, roll)
        elif isinstance(space, SpecialSpace):
            self._handle_special_space(player, space)
    
    def _handle_property(self, player: Player, prop: Property, roll: DiceRoll) -> None:
        """Handle landing on a property."""
        if prop.owner is None:
            # Unowned - offer to buy
            self._offer_property(player, prop)
        elif prop.owner == player:
            print(f"  You own {prop.name}.")
        elif prop.is_mortgaged:
            print(f"  {prop.name} is mortgaged. No rent owed.")
        else:
            # Pay rent
            rent = prop.calculate_rent(roll.total)
            print(f"  💰 Owe ${rent} rent to {prop.owner.name}")
            if not player.pay_to(prop.owner, rent):
                self._handle_bankruptcy(player, prop.owner, rent)
    
    def _offer_property(self, player: Player, prop: Property) -> None:
        """Offer an unowned property to the player."""
        print(f"\n  🏠 {prop.name} is available for ${prop.price}")
        
        if player.money >= prop.price:
            # Auto-buy for simplicity (can be made interactive)
            response = input(f"  Buy for ${prop.price}? (y/n): ").strip().lower()
            if response == 'y':
                player.pay(prop.price)
                player.add_property(prop)
                print(f"  ✅ {player.name} bought {prop.name}!")
            else:
                print(f"  {player.name} declined to buy {prop.name}.")
        else:
            print(f"  Insufficient funds (${player.money})")
    
    def _handle_special_space(self, player: Player, space: SpecialSpace) -> None:
        """Handle landing on a special space."""
        match space.space_type:
            case SpaceType.GO:
                print("  Welcome to GO!")
            
            case SpaceType.JAIL:
                print("  Just visiting jail.")
            
            case SpaceType.FREE_PARKING:
                print("  🅿️ Free Parking. Nothing happens.")
            
            case SpaceType.GO_TO_JAIL:
                self.send_to_jail(player)
            
            case SpaceType.CHANCE:
                self._draw_card(player, self.chance_deck)
            
            case SpaceType.COMMUNITY_CHEST:
                self._draw_card(player, self.community_chest_deck)
            
            case SpaceType.INCOME_TAX:
                tax = min(200, int(player.money * 0.1))
                print(f"  💸 Income Tax: ${tax}")
                if not player.pay(tax):
                    self._handle_bankruptcy(player, None, tax)
            
            case SpaceType.LUXURY_TAX:
                print("  💎 Luxury Tax: $100")
                if not player.pay(100):
                    self._handle_bankruptcy(player, None, 100)
    
    def _draw_card(self, player: Player, deck: CardDeck) -> None:
        """Draw and execute a card."""
        card = deck.draw()
        print(f"\n  🃏 {deck.card_type.value}: {card.description}")
        card.execute(self, player)
    
    def send_to_jail(self, player: Player) -> None:
        """Send a player directly to jail."""
        player.go_to_jail()
        self.dice.reset_doubles()
    
    def move_player(self, player: Player, spaces: int) -> None:
        """Move player by a number of spaces."""
        passed_go = player.move(spaces)
        if passed_go:
            player.receive(200)
        self._handle_space(player, self.last_dice_roll or DiceRoll(0, 0))
    
    def move_player_to(self, player: Player, position: int) -> None:
        """Move player to a specific position."""
        passed_go = player.move_to(position)
        if passed_go:
            player.receive(200)
        self._handle_space(player, self.last_dice_roll or DiceRoll(0, 0))
    
    def advance_to_nearest_utility(self, player: Player) -> None:
        """Advance to nearest utility (for Chance card)."""
        pos = self.board.find_nearest_utility(player.position)
        passed_go = player.move_to(pos)
        if passed_go:
            player.receive(200)
        
        utility = self.board.get_property(pos)
        if utility and utility.owner and utility.owner != player:
            # Pay 10x dice roll
            rent = self.last_dice_roll.total * 10
            print(f"  Must pay 10x dice roll = ${rent}")
            if not player.pay_to(utility.owner, rent):
                self._handle_bankruptcy(player, utility.owner, rent)
        else:
            self._handle_space(player, self.last_dice_roll or DiceRoll(0, 0))
    
    def advance_to_nearest_railroad(self, player: Player) -> None:
        """Advance to nearest railroad (for Chance card)."""
        pos = self.board.find_nearest_railroad(player.position)
        passed_go = player.move_to(pos)
        if passed_go:
            player.receive(200)
        
        railroad = self.board.get_property(pos)
        if railroad and railroad.owner and railroad.owner != player:
            # Pay double rent
            rent = railroad.calculate_rent() * 2
            print(f"  Must pay double rent = ${rent}")
            if not player.pay_to(railroad.owner, rent):
                self._handle_bankruptcy(player, railroad.owner, rent)
        else:
            self._handle_space(player, self.last_dice_roll or DiceRoll(0, 0))
    
    def pay_each_player(self, payer: Player, amount: int) -> None:
        """Pay each other player a specified amount."""
        for player in self.active_players:
            if player != payer:
                if not payer.pay_to(player, amount):
                    self._handle_bankruptcy(payer, player, amount)
                    return
    
    def collect_from_each_player(self, collector: Player, amount: int) -> None:
        """Collect a specified amount from each other player."""
        for player in self.active_players:
            if player != collector:
                player.pay_to(collector, amount)
    
    def _handle_bankruptcy(self, player: Player, creditor: Optional[Player], debt: int) -> None:
        """Handle a player going bankrupt."""
        print(f"\n  ⚠️ {player.name} cannot pay ${debt}!")
        
        total_assets = player.total_assets()
        if total_assets < debt:
            player.declare_bankruptcy(creditor)
            self._check_winner()
        else:
            print(f"  Must sell houses/mortgage properties to raise ${debt - player.money}")
            # Simplified: auto-liquidate
            self._auto_liquidate(player, debt - player.money)
    
    def _auto_liquidate(self, player: Player, needed: int) -> None:
        """Auto-sell assets to raise needed funds."""
        # Sell houses first
        for prop in player.properties:
            if isinstance(prop, Street) and prop.houses > 0:
                while prop.houses > 0 and player.money < needed:
                    amount = prop.sell_house()
                    player.receive(amount)
                    self.bank.return_house()
        
        # Mortgage properties
        for prop in player.properties:
            if not prop.is_mortgaged and player.money < needed:
                amount = prop.mortgage()
                player.receive(amount)
    
    def _check_winner(self) -> None:
        """Check if there's a winner (only one player remaining)."""
        active = self.active_players
        if len(active) == 1:
            self.winner = active[0]
            self.game_over = True
            print(f"\n{'='*50}")
            print(f"  🏆 {self.winner.name} WINS! 🏆")
            print(f"{'='*50}")
    
    def run(self) -> Player:
        """
        Run the game until completion.
        
        Returns:
            The winning player.
        """
        if len(self.players) < 2:
            raise ValueError("Need at least 2 players")
        
        print("\n" + "="*50)
        print("  🎲 MONOPOLY GAME STARTING! 🎲")
        print("="*50)
        
        for player in self.players:
            print(f"  {player.token} {player.name}")
        
        while not self.game_over:
            # Play turn (may repeat if doubles)
            while self.play_turn():
                pass
            
            # Check for winner after each turn
            if not self.game_over:
                self.next_turn()
            
            # Safety limit for testing
            if self.turn_count > 1000:
                print("Game limit reached!")
                break
        
        return self.winner
