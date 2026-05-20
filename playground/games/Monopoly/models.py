"""
models.py - Core data models for Monopoly
All classes are designed to be fully serializable to/from dict for save/load support.
"""

class Player:
    def __init__(self, name, is_ai=False):
        self.name = name
        self.is_ai = is_ai
        self.money = 1500
        self.position = 0
        self.in_jail = False
        self.jail_turns = 0         # how many turns spent in jail (max 3)
        self.get_out_of_jail_free_cards = 0
        self.properties = []        # list of PropertySpace objects owned
        self.is_bankrupt = False

    def add_money(self, amount):
        self.money += amount

    def pay_money(self, amount):
        """Returns True if payment succeeded, False if insufficient funds."""
        if self.money >= amount:
            self.money -= amount
            return True
        return False

    def net_worth(self):
        """Total assets: cash + property prices + house values (half mortgage value)."""
        total = self.money
        for prop in self.properties:
            total += prop.price // 2  # mortgage value
            if prop.color not in ["Station", "Utility"]:
                total += prop.houses * prop.build_cost // 2
        return total

    def move(self, steps):
        """Move player by steps. Returns True if passed GO."""
        old_pos = self.position
        self.position = (self.position + steps) % 40
        # Passed GO if position wrapped around (new pos < old pos OR old+steps >= 40)
        return old_pos + steps >= 40

    def can_afford(self, amount):
        return self.money >= amount

    def to_dict(self):
        return {
            "name": self.name,
            "is_ai": self.is_ai,
            "money": self.money,
            "position": self.position,
            "in_jail": self.in_jail,
            "jail_turns": self.jail_turns,
            "get_out_of_jail_free_cards": self.get_out_of_jail_free_cards,
            "property_indices": [p.index for p in self.properties],
            "is_bankrupt": self.is_bankrupt,
        }

    @classmethod
    def from_dict(cls, data):
        p = cls(data["name"], data["is_ai"])
        p.money = data["money"]
        p.position = data["position"]
        p.in_jail = data["in_jail"]
        p.jail_turns = data["jail_turns"]
        p.get_out_of_jail_free_cards = data["get_out_of_jail_free_cards"]
        p.is_bankrupt = data["is_bankrupt"]
        # properties are restored by the engine using property_indices
        return p


class Space:
    def __init__(self, index, name):
        self.index = index
        self.name = name


class PropertySpace(Space):
    """Represents a purchasable space: street, railroad, or utility."""
    def __init__(self, index, name, color, price, rent_data, build_cost=0):
        super().__init__(index, name)
        self.color = color
        self.price = price
        # rent_data: [base, 1house, 2house, 3house, 4house, hotel]
        # For Station/Utility: rent_data is [] (computed separately)
        self.rent_data = rent_data
        self.build_cost = build_cost
        self.owner = None           # reference to Player object
        self.houses = 0             # 0-4 = houses, 5 = hotel
        self.is_mortgaged = False

    def get_rent(self, all_properties, dice_roll=0):
        """
        Calculate rent based on ownership context.
        all_properties: full board list (needed for monopoly/station count checks)
        dice_roll: total dice value (used by utility calculation)
        """
        if self.is_mortgaged or self.owner is None:
            return 0

        if self.color == "Utility":
            owned_utils = sum(
                1 for p in all_properties
                if isinstance(p, PropertySpace)
                and p.color == "Utility"
                and p.owner == self.owner
            )
            multiplier = 10 if owned_utils == 2 else 4
            return dice_roll * multiplier

        if self.color == "Station":
            owned_stations = sum(
                1 for p in all_properties
                if isinstance(p, PropertySpace)
                and p.color == "Station"
                and p.owner == self.owner
            )
            return 25 * (2 ** (owned_stations - 1))

        # Street property
        if self.houses > 0:
            return self.rent_data[self.houses]  # index 1-5

        # Check monopoly (all same-color owned by same player, no mortgage)
        same_color = [
            p for p in all_properties
            if isinstance(p, PropertySpace) and p.color == self.color
        ]
        has_monopoly = all(p.owner == self.owner and not p.is_mortgaged for p in same_color)
        base_rent = self.rent_data[0]
        return base_rent * 2 if has_monopoly else base_rent

    def mortgage_value(self):
        return self.price // 2

    def unmortgage_cost(self):
        return int(self.price // 2 * 1.1)

    def can_build(self, all_properties):
        """Check if a house can be built on this property (even-build rule)."""
        if self.color in ["Station", "Utility"]:
            return False
        if self.is_mortgaged:
            return False
        same_color = [
            p for p in all_properties
            if isinstance(p, PropertySpace) and p.color == self.color
        ]
        # Must own all of same color
        if not all(p.owner == self.owner for p in same_color):
            return False
        # Must have no mortgaged properties in set
        if any(p.is_mortgaged for p in same_color):
            return False
        # Even-build: this property must have the fewest houses
        min_houses = min(p.houses for p in same_color)
        return self.houses == min_houses and self.houses < 5

    def can_sell_house(self, all_properties):
        """Check if a house can be sold (even-sell rule)."""
        if self.houses == 0:
            return False
        same_color = [
            p for p in all_properties
            if isinstance(p, PropertySpace) and p.color == self.color
        ]
        max_houses = max(p.houses for p in same_color)
        return self.houses == max_houses

    def to_dict(self):
        return {
            "index": self.index,
            "owner_name": self.owner.name if self.owner else None,
            "houses": self.houses,
            "is_mortgaged": self.is_mortgaged,
        }


class TaxSpace(Space):
    def __init__(self, index, name, tax_amount):
        super().__init__(index, name)
        self.tax_amount = tax_amount


class CardSpace(Space):
    def __init__(self, index, name, card_type):
        super().__init__(index, name)
        self.card_type = card_type


class ActionSpace(Space):
    def __init__(self, index, name, action_type):
        super().__init__(index, name)
        self.action_type = action_type


class Card:
    def __init__(self, id_str, text, action_type, **kwargs):
        self.id_str = id_str
        self.text = text
        self.action_type = action_type
        self.params = kwargs

    def to_dict(self):
        return {"id_str": self.id_str}


class Bank:
    def __init__(self):
        self.houses = 32
        self.hotels = 12

    def to_dict(self):
        return {"houses": self.houses, "hotels": self.hotels}

    def from_dict(self, data):
        self.houses = data["houses"]
        self.hotels = data["hotels"]
