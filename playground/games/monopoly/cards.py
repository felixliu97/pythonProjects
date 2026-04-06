"""
Cards module for Monopoly game.

Contains Chance and Community Chest card definitions and deck management.
"""

import random
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .game import MonopolyGame
    from .player import Player


class CardType(Enum):
    """Types of card decks."""
    CHANCE = "Chance"
    COMMUNITY_CHEST = "Community Chest"


@dataclass
class Card:
    """
    Represents a Chance or Community Chest card.
    
    Attributes:
        description: Text shown when card is drawn.
        action: Function to execute the card's effect.
        keep: Whether player can keep this card (Get Out of Jail Free).
    """
    description: str
    action: Callable[["MonopolyGame", "Player"], None]
    keep: bool = False
    
    def execute(self, game: "MonopolyGame", player: "Player") -> None:
        """Execute this card's action."""
        self.action(game, player)


class CardDeck:
    """
    Manages a deck of cards (Chance or Community Chest).
    
    Cards are shuffled and drawn from the top. Get Out of Jail Free
    cards are removed when drawn and returned when used.
    """
    
    def __init__(self, card_type: CardType):
        self.card_type = card_type
        self.cards: list[Card] = []
        self.discard: list[Card] = []
        self._initialize_deck()
        self.shuffle()
    
    def _initialize_deck(self) -> None:
        """Create all cards for this deck type."""
        if self.card_type == CardType.CHANCE:
            self._create_chance_cards()
        else:
            self._create_community_chest_cards()
    
    def _create_chance_cards(self) -> None:
        """Create the 16 Chance cards."""
        self.cards = [
            Card("Advance to GO. Collect $200.", 
                 lambda g, p: (p.move_to(0), p.receive(200))),
            Card("Advance to Illinois Avenue.",
                 lambda g, p: g.move_player_to(p, 24)),
            Card("Advance to St. Charles Place.",
                 lambda g, p: g.move_player_to(p, 11)),
            Card("Advance to nearest Utility. Pay 10x dice roll.",
                 lambda g, p: g.advance_to_nearest_utility(p)),
            Card("Advance to nearest Railroad. Pay double rent.",
                 lambda g, p: g.advance_to_nearest_railroad(p)),
            Card("Bank pays you dividend of $50.",
                 lambda g, p: p.receive(50)),
            Card("Get Out of Jail Free.",
                 lambda g, p: p.add_jail_card(CardType.CHANCE), keep=True),
            Card("Go back 3 spaces.",
                 lambda g, p: g.move_player(p, -3)),
            Card("Go to Jail. Do not pass GO.",
                 lambda g, p: g.send_to_jail(p)),
            Card("Make general repairs: $25/house, $100/hotel.",
                 lambda g, p: p.pay(p.calculate_repairs(25, 100))),
            Card("Pay poor tax of $15.",
                 lambda g, p: p.pay(15)),
            Card("Take a trip to Reading Railroad.",
                 lambda g, p: g.move_player_to(p, 5)),
            Card("Take a walk on the Boardwalk.",
                 lambda g, p: g.move_player_to(p, 39)),
            Card("You have been elected Chairman. Pay each player $50.",
                 lambda g, p: g.pay_each_player(p, 50)),
            Card("Your building loan matures. Collect $150.",
                 lambda g, p: p.receive(150)),
            Card("You have won a crossword competition. Collect $100.",
                 lambda g, p: p.receive(100)),
        ]
    
    def _create_community_chest_cards(self) -> None:
        """Create the 16 Community Chest cards."""
        self.cards = [
            Card("Advance to GO. Collect $200.",
                 lambda g, p: (p.move_to(0), p.receive(200))),
            Card("Bank error in your favor. Collect $200.",
                 lambda g, p: p.receive(200)),
            Card("Doctor's fees. Pay $50.",
                 lambda g, p: p.pay(50)),
            Card("From sale of stock you get $50.",
                 lambda g, p: p.receive(50)),
            Card("Get Out of Jail Free.",
                 lambda g, p: p.add_jail_card(CardType.COMMUNITY_CHEST), keep=True),
            Card("Go to Jail. Do not pass GO.",
                 lambda g, p: g.send_to_jail(p)),
            Card("Grand Opera Night. Collect $50 from every player.",
                 lambda g, p: g.collect_from_each_player(p, 50)),
            Card("Holiday Fund matures. Collect $100.",
                 lambda g, p: p.receive(100)),
            Card("Income tax refund. Collect $20.",
                 lambda g, p: p.receive(20)),
            Card("It's your birthday. Collect $10 from every player.",
                 lambda g, p: g.collect_from_each_player(p, 10)),
            Card("Life insurance matures. Collect $100.",
                 lambda g, p: p.receive(100)),
            Card("Hospital fees. Pay $100.",
                 lambda g, p: p.pay(100)),
            Card("School fees. Pay $50.",
                 lambda g, p: p.pay(50)),
            Card("Receive $25 consultancy fee.",
                 lambda g, p: p.receive(25)),
            Card("You are assessed for street repairs: $40/house, $115/hotel.",
                 lambda g, p: p.pay(p.calculate_repairs(40, 115))),
            Card("You have won second prize in a beauty contest. Collect $10.",
                 lambda g, p: p.receive(10)),
        ]
    
    def shuffle(self) -> None:
        """Shuffle the deck."""
        self.cards.extend(self.discard)
        self.discard.clear()
        random.shuffle(self.cards)
    
    def draw(self) -> Card:
        """
        Draw a card from the deck.
        
        Returns:
            The drawn card.
        """
        if not self.cards:
            self.shuffle()
        
        card = self.cards.pop(0)
        if not card.keep:
            self.discard.append(card)
        return card
    
    def return_card(self, card: Card) -> None:
        """Return a kept card (Get Out of Jail Free) to the deck."""
        self.discard.append(card)
