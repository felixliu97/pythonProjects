"""
Command-Line Interface for Monopoly game.

Provides text-based interaction for playing Monopoly.
"""

from typing import Optional
from .game import MonopolyGame
from .player import Player
from .property import Property, Street


class MonopolyCLI:
    """
    Command-line interface for playing Monopoly.
    
    Handles user input and displays game state.
    """
    
    def __init__(self):
        self.game = MonopolyGame()
    
    def setup_players(self) -> None:
        """Prompt for player setup."""
        print("\n" + "="*50)
        print("  🎩 MONOPOLY - Player Setup")
        print("="*50)
        
        tokens = ["🎩", "🚗", "🐕", "⛵"]
        
        while True:
            try:
                num_players = int(input("\nHow many players? (2-4): "))
                if 2 <= num_players <= 4:
                    break
                print("Please enter a number between 2 and 4.")
            except ValueError:
                print("Please enter a valid number.")
        
        for i in range(num_players):
            name = input(f"\nPlayer {i+1} name: ").strip()
            if not name:
                name = f"Player {i+1}"
            token = tokens[i]
            player = self.game.add_player(name, token)
            print(f"  {token} {name} joined the game!")
    
    def show_status(self) -> None:
        """Display current game status."""
        print("\n" + "-"*40)
        print("  PLAYER STATUS")
        print("-"*40)
        for player in self.game.players:
            status = "💀 BANKRUPT" if player.is_bankrupt else ""
            jail_status = "🔒 IN JAIL" if player.in_jail else ""
            print(f"  {player.token} {player.name}: ${player.money} "
                  f"(Pos {player.position}) {jail_status} {status}")
    
    def show_properties(self, player: Player) -> None:
        """Display a player's properties."""
        if not player.properties:
            print(f"\n  {player.name} owns no properties.")
            return
        
        print(f"\n  {player.name}'s Properties:")
        for prop in player.properties:
            status = "[MORTGAGED]" if prop.is_mortgaged else ""
            houses = ""
            if isinstance(prop, Street):
                if prop.has_hotel:
                    houses = " 🏨"
                elif prop.houses > 0:
                    houses = " " + "🏠" * prop.houses
            print(f"    - {prop.name} {houses} {status}")
    
    def player_menu(self, player: Player) -> None:
        """Show action menu for current player."""
        while True:
            print(f"\n  Actions for {player.name}:")
            print("  1. Roll dice")
            print("  2. View properties")
            print("  3. Build house")
            print("  4. Mortgage property")
            print("  5. End turn")
            
            choice = input("  Choose action (1-5): ").strip()
            
            match choice:
                case "1":
                    return  # Proceed with turn
                case "2":
                    self.show_properties(player)
                case "3":
                    self.build_house_menu(player)
                case "4":
                    self.mortgage_menu(player)
                case "5":
                    return
                case _:
                    print("  Invalid choice.")
    
    def build_house_menu(self, player: Player) -> None:
        """Menu for building houses."""
        buildable = [p for p in player.properties 
                     if isinstance(p, Street) and p.can_build()]
        
        if not buildable:
            print("  No properties available for building.")
            return
        
        print("\n  Buildable properties:")
        for i, prop in enumerate(buildable, 1):
            print(f"  {i}. {prop.name} ({prop.houses} houses) - ${prop.house_cost}")
        
        try:
            choice = int(input("  Choose property (0 to cancel): "))
            if 1 <= choice <= len(buildable):
                prop = buildable[choice - 1]
                if player.money >= prop.house_cost:
                    if self.game.bank.sell_house():
                        cost = prop.build_house()
                        player.pay(cost)
                        print(f"  🏠 Built house on {prop.name}!")
                else:
                    print("  Insufficient funds.")
        except (ValueError, IndexError):
            pass
    
    def mortgage_menu(self, player: Player) -> None:
        """Menu for mortgaging properties."""
        mortgageable = [p for p in player.properties if not p.is_mortgaged]
        
        if not mortgageable:
            print("  No properties available to mortgage.")
            return
        
        print("\n  Properties to mortgage:")
        for i, prop in enumerate(mortgageable, 1):
            print(f"  {i}. {prop.name} - Receive ${prop.mortgage_value}")
        
        try:
            choice = int(input("  Choose property (0 to cancel): "))
            if 1 <= choice <= len(mortgageable):
                prop = mortgageable[choice - 1]
                amount = prop.mortgage()
                player.receive(amount)
                print(f"  📋 Mortgaged {prop.name} for ${amount}!")
        except (ValueError, IndexError):
            pass
    
    def run(self) -> None:
        """Run the complete game."""
        print("\n" + "="*50)
        print("  🎲 WELCOME TO MONOPOLY! 🎲")
        print("="*50)
        
        self.setup_players()
        
        print("\n" + "="*50)
        print("  GAME STARTING!")
        print("="*50)
        
        self.show_status()
        
        # Run game
        winner = self.game.run()
        
        print("\n" + "="*50)
        print("  GAME OVER!")
        print("="*50)
        
        if winner:
            print(f"\n  🏆 {winner.name} is the WINNER! 🏆")
            print(f"  Final wealth: ${winner.money}")
            print(f"  Properties owned: {len(winner.properties)}")
        
        self.show_status()


def main():
    """Entry point for the Monopoly game."""
    cli = MonopolyCLI()
    cli.run()


if __name__ == "__main__":
    main()
