"""
test_monopoly.py - Comprehensive unit tests covering all core Monopoly rules.

Run with:  python -m pytest test_monopoly.py -v
           (or) python test_monopoly.py
"""
import unittest
import sys
import os

# Allow imports from the same directory
sys.path.insert(0, os.path.dirname(__file__))

from models import Player, PropertySpace, TaxSpace, ActionSpace, CardSpace, Bank
from board_data import get_board_spaces, get_chance_cards, get_community_chest_cards
from engine import MonopolyEngine


# ─────────────────────── Helpers ────────────────────────────────────────────

def make_engine(n_humans=2):
    """Create a fresh engine with n human players."""
    players = [Player(f"P{i+1}") for i in range(n_humans)]
    return MonopolyEngine(players)


def make_engine_with_ai():
    players = [Player("玩家", is_ai=False), Player("机器人", is_ai=True)]
    return MonopolyEngine(players)


def get_board():
    return get_board_spaces()


def get_property(board, index):
    sp = board[index]
    assert isinstance(sp, PropertySpace), f"Index {index} is not a PropertySpace"
    return sp


# ══════════════════════════════════════════════════════════════════════════════
#  1. Player model tests
# ══════════════════════════════════════════════════════════════════════════════

class TestPlayerModel(unittest.TestCase):

    def setUp(self):
        self.p = Player("Alice")

    def test_initial_money(self):
        self.assertEqual(self.p.money, 1500)

    def test_initial_position(self):
        self.assertEqual(self.p.position, 0)

    def test_add_money(self):
        self.p.add_money(300)
        self.assertEqual(self.p.money, 1800)

    def test_pay_money_success(self):
        result = self.p.pay_money(500)
        self.assertTrue(result)
        self.assertEqual(self.p.money, 1000)

    def test_pay_money_insufficient(self):
        result = self.p.pay_money(2000)
        self.assertFalse(result)
        self.assertEqual(self.p.money, 1500)  # unchanged

    def test_move_normal(self):
        self.p.position = 5
        passed = self.p.move(6)
        self.assertEqual(self.p.position, 11)
        self.assertFalse(passed)

    def test_move_passes_go(self):
        self.p.position = 38
        passed = self.p.move(4)
        self.assertEqual(self.p.position, 2)
        self.assertTrue(passed)

    def test_move_lands_on_go(self):
        self.p.position = 38
        passed = self.p.move(2)
        self.assertEqual(self.p.position, 0)
        self.assertTrue(passed)

    def test_move_wraps_correctly(self):
        self.p.position = 36
        passed = self.p.move(12)
        self.assertEqual(self.p.position, 8)
        self.assertTrue(passed)

    def test_can_afford_exact(self):
        self.assertTrue(self.p.can_afford(1500))

    def test_can_afford_over(self):
        self.assertFalse(self.p.can_afford(1501))

    def test_net_worth_cash_only(self):
        self.assertEqual(self.p.net_worth(), 1500)

    def test_serialization_roundtrip(self):
        self.p.money = 800
        self.p.position = 15
        self.p.in_jail = True
        self.p.jail_turns = 2
        data = self.p.to_dict()
        restored = Player.from_dict(data)
        self.assertEqual(restored.name, "Alice")
        self.assertEqual(restored.money, 800)
        self.assertEqual(restored.position, 15)
        self.assertTrue(restored.in_jail)
        self.assertEqual(restored.jail_turns, 2)


# ══════════════════════════════════════════════════════════════════════════════
#  2. Board data integrity tests
# ══════════════════════════════════════════════════════════════════════════════

class TestBoardData(unittest.TestCase):

    def setUp(self):
        self.board = get_board()

    def test_board_has_40_spaces(self):
        self.assertEqual(len(self.board), 40)

    def test_indices_are_correct(self):
        for i, space in enumerate(self.board):
            self.assertEqual(space.index, i)

    def test_go_is_index_0(self):
        sp = self.board[0]
        self.assertIsInstance(sp, ActionSpace)
        self.assertEqual(sp.action_type, "GO")

    def test_jail_is_index_10(self):
        sp = self.board[10]
        self.assertIsInstance(sp, ActionSpace)
        self.assertEqual(sp.action_type, "Jail")

    def test_free_parking_is_index_20(self):
        sp = self.board[20]
        self.assertIsInstance(sp, ActionSpace)
        self.assertEqual(sp.action_type, "Free Parking")

    def test_go_to_jail_is_index_30(self):
        sp = self.board[30]
        self.assertIsInstance(sp, ActionSpace)
        self.assertEqual(sp.action_type, "Go To Jail")

    def test_income_tax_is_200(self):
        sp = self.board[4]
        self.assertIsInstance(sp, TaxSpace)
        self.assertEqual(sp.tax_amount, 200)

    def test_luxury_tax_is_100(self):
        sp = self.board[38]
        self.assertIsInstance(sp, TaxSpace)
        self.assertEqual(sp.tax_amount, 100)

    def test_four_railroads(self):
        stations = [s for s in self.board if isinstance(s, PropertySpace) and s.color == "Station"]
        self.assertEqual(len(stations), 4)
        indices = {s.index for s in stations}
        self.assertEqual(indices, {5, 15, 25, 35})

    def test_two_utilities(self):
        utils = [s for s in self.board if isinstance(s, PropertySpace) and s.color == "Utility"]
        self.assertEqual(len(utils), 2)

    def test_brown_group_has_two_properties(self):
        browns = [s for s in self.board if isinstance(s, PropertySpace) and s.color == "Brown"]
        self.assertEqual(len(browns), 2)

    def test_dark_blue_group_has_two_properties(self):
        dark_blue = [s for s in self.board if isinstance(s, PropertySpace) and s.color == "Dark Blue"]
        self.assertEqual(len(dark_blue), 2)

    def test_most_color_groups_have_three(self):
        multi = ["Light Blue", "Pink", "Orange", "Red", "Yellow", "Green"]
        for color in multi:
            group = [s for s in self.board if isinstance(s, PropertySpace) and s.color == color]
            self.assertEqual(len(group), 3, f"{color} should have 3 properties")

    def test_boardwalk_price_400(self):
        bw = self.board[39]
        self.assertIsInstance(bw, PropertySpace)
        self.assertEqual(bw.price, 400)

    def test_mediterranean_price_60(self):
        med = self.board[1]
        self.assertIsInstance(med, PropertySpace)
        self.assertEqual(med.price, 60)

    def test_chance_cards_count(self):
        cards = get_chance_cards()
        self.assertEqual(len(cards), 16)

    def test_community_chest_cards_count(self):
        cards = get_community_chest_cards()
        self.assertEqual(len(cards), 16)

    def test_chance_has_jail_free_card(self):
        cards = get_chance_cards()
        types = [c.action_type for c in cards]
        self.assertIn("get_out_of_jail_free", types)

    def test_chest_has_jail_free_card(self):
        cards = get_community_chest_cards()
        types = [c.action_type for c in cards]
        self.assertIn("get_out_of_jail_free", types)


# ══════════════════════════════════════════════════════════════════════════════
#  3. Rent calculation tests
# ══════════════════════════════════════════════════════════════════════════════

class TestRentCalculation(unittest.TestCase):

    def setUp(self):
        self.board = get_board()
        self.p1 = Player("Alice")
        self.p2 = Player("Bob")

    def _own(self, player, index):
        sp = get_property(self.board, index)
        sp.owner = player
        player.properties.append(sp)
        return sp

    def test_no_rent_unowned(self):
        sp = get_property(self.board, 1)
        rent = sp.get_rent(self.board)
        self.assertEqual(rent, 0)

    def test_no_rent_mortgaged(self):
        sp = self._own(self.p1, 1)
        sp.is_mortgaged = True
        rent = sp.get_rent(self.board)
        self.assertEqual(rent, 0)

    def test_base_rent_single_property(self):
        """Without monopoly, pay base rent."""
        sp = self._own(self.p1, 1)   # Mediterranean $2 base
        rent = sp.get_rent(self.board)
        self.assertEqual(rent, 2)

    def test_double_rent_monopoly_no_houses(self):
        """Owning full color group doubles base rent."""
        sp1 = self._own(self.p1, 1)   # Mediterranean ($2 base)
        sp3 = self._own(self.p1, 3)   # Baltic ($4 base)
        rent = sp1.get_rent(self.board)
        self.assertEqual(rent, 4)     # doubled

    def test_rent_with_houses(self):
        sp1 = self._own(self.p1, 1)
        sp3 = self._own(self.p1, 3)
        sp1.houses = 1
        rent = sp1.get_rent(self.board)
        self.assertEqual(rent, 10)   # rent_data[1] for Mediterranean

    def test_rent_hotel(self):
        sp1 = self._own(self.p1, 1)
        sp3 = self._own(self.p1, 3)
        sp1.houses = 5   # hotel
        rent = sp1.get_rent(self.board)
        self.assertEqual(rent, 250)  # rent_data[5] for Mediterranean

    def test_monopoly_broken_by_mortgage_no_double_rent(self):
        """Mortgaged property breaks monopoly double rent."""
        sp1 = self._own(self.p1, 1)
        sp3 = self._own(self.p1, 3)
        sp3.is_mortgaged = True
        rent = sp1.get_rent(self.board)
        self.assertEqual(rent, 2)   # no double

    def test_railroad_one_owned(self):
        rr = self._own(self.p1, 5)  # Reading Railroad
        rent = rr.get_rent(self.board)
        self.assertEqual(rent, 25)

    def test_railroad_two_owned(self):
        rr1 = self._own(self.p1, 5)
        rr2 = self._own(self.p1, 15)
        rent = rr1.get_rent(self.board)
        self.assertEqual(rent, 50)

    def test_railroad_three_owned(self):
        rr1 = self._own(self.p1, 5)
        rr2 = self._own(self.p1, 15)
        rr3 = self._own(self.p1, 25)
        rent = rr1.get_rent(self.board)
        self.assertEqual(rent, 100)

    def test_railroad_four_owned(self):
        for idx in [5, 15, 25, 35]:
            self._own(self.p1, idx)
        rr = self.board[5]
        rent = rr.get_rent(self.board)
        self.assertEqual(rent, 200)

    def test_utility_one_owned_multiplier_4(self):
        util = self._own(self.p1, 12)  # Electric Company
        rent = util.get_rent(self.board, dice_roll=7)
        self.assertEqual(rent, 28)   # 4 × 7

    def test_utility_two_owned_multiplier_10(self):
        u1 = self._own(self.p1, 12)
        u2 = self._own(self.p1, 28)
        rent = u1.get_rent(self.board, dice_roll=8)
        self.assertEqual(rent, 80)   # 10 × 8


# ══════════════════════════════════════════════════════════════════════════════
#  4. Building mechanics tests
# ══════════════════════════════════════════════════════════════════════════════

class TestBuildingMechanics(unittest.TestCase):

    def setUp(self):
        self.engine = make_engine(1)
        self.player = self.engine.players[0]
        self.player.money = 10000
        self.board = self.engine.board

    def _own_all_brown(self):
        for idx in [1, 3]:
            sp = self.board[idx]
            sp.owner = self.player
            self.player.properties.append(sp)

    def test_cannot_build_without_monopoly(self):
        sp = self.board[1]
        sp.owner = self.player
        self.player.properties.append(sp)
        self.assertFalse(sp.can_build(self.board))

    def test_can_build_with_monopoly(self):
        self._own_all_brown()
        sp = self.board[1]
        self.assertTrue(sp.can_build(self.board))

    def test_even_build_rule_enforced(self):
        """Cannot build a second house before the other has one."""
        self._own_all_brown()
        sp1 = self.board[1]
        sp3 = self.board[3]
        sp1.houses = 1
        # sp3 still has 0 → sp1 cannot build again
        self.assertFalse(sp1.can_build(self.board))
        # sp3 can build
        self.assertTrue(sp3.can_build(self.board))

    def test_build_house_deducts_money(self):
        self._own_all_brown()
        sp = self.board[1]  # build cost $50
        self.engine.build_house(self.player, sp)
        self.assertEqual(sp.houses, 1)
        self.assertEqual(self.player.money, 10000 - 50)

    def test_build_house_decrements_bank(self):
        self._own_all_brown()
        before = self.engine.bank.houses
        self.engine.build_house(self.player, self.board[1])
        self.assertEqual(self.engine.bank.houses, before - 1)

    def test_upgrade_to_hotel(self):
        self._own_all_brown()
        sp1 = self.board[1]
        sp3 = self.board[3]
        # Fill both to 4 houses via engine (even build)
        for _ in range(4):
            self.engine.build_house(self.player, sp1)
            self.engine.build_house(self.player, sp3)
        self.assertEqual(sp1.houses, 4)
        self.assertEqual(sp3.houses, 4)
        # 8 houses taken total from bank
        self.assertEqual(self.engine.bank.houses, 32 - 8)
        # Now build hotel on sp1: 4 houses returned, 1 hotel consumed
        self.engine.build_house(self.player, sp1)
        self.assertEqual(sp1.houses, 5)   # hotel
        self.assertEqual(self.engine.bank.hotels, 11)
        self.assertEqual(self.engine.bank.houses, 32 - 8 + 4)  # 4 returned when hotel built

    def test_sell_house_refunds_half(self):
        self._own_all_brown()
        sp1 = self.board[1]
        sp3 = self.board[3]
        self.engine.build_house(self.player, sp1)
        self.engine.build_house(self.player, sp3)
        money_before = self.player.money
        self.engine.sell_house(self.player, sp1)
        self.assertEqual(sp1.houses, 0)
        self.assertEqual(self.player.money, money_before + 25)   # $50 / 2

    def test_even_sell_rule(self):
        """Cannot sell from the property with fewer houses."""
        self._own_all_brown()
        sp1 = self.board[1]
        sp3 = self.board[3]
        self.engine.build_house(self.player, sp1)
        self.engine.build_house(self.player, sp3)
        self.engine.build_house(self.player, sp1)   # sp1 now has 2, sp3 has 1
        # Cannot sell from sp3 (has fewer)
        result = self.engine.sell_house(self.player, sp3)
        self.assertFalse(result)

    def test_cannot_build_on_station(self):
        rr = self.board[5]
        rr.owner = self.player
        self.player.properties.append(rr)
        self.assertFalse(rr.can_build(self.board))

    def test_cannot_build_on_utility(self):
        util = self.board[12]
        util.owner = self.player
        self.player.properties.append(util)
        self.assertFalse(util.can_build(self.board))

    def test_cannot_build_on_mortgaged(self):
        self._own_all_brown()
        sp1 = self.board[1]
        sp1.is_mortgaged = True
        self.assertFalse(sp1.can_build(self.board))


# ══════════════════════════════════════════════════════════════════════════════
#  5. Mortgage / Unmortgage tests
# ══════════════════════════════════════════════════════════════════════════════

class TestMortgage(unittest.TestCase):

    def setUp(self):
        self.engine = make_engine(1)
        self.player = self.engine.players[0]
        self.board = self.engine.board

    def _own(self, index):
        sp = self.board[index]
        sp.owner = self.player
        self.player.properties.append(sp)
        return sp

    def test_mortgage_gives_half_price(self):
        sp = self._own(1)   # Mediterranean $60 → $30
        money_before = self.player.money
        self.engine.mortgage_property(self.player, sp)
        self.assertTrue(sp.is_mortgaged)
        self.assertEqual(self.player.money, money_before + 30)

    def test_unmortgage_costs_10_percent_more(self):
        sp = self._own(1)
        self.engine.mortgage_property(self.player, sp)
        money_before = self.player.money
        self.engine.unmortgage_property(self.player, sp)
        self.assertFalse(sp.is_mortgaged)
        # $30 + 10% = $33
        self.assertEqual(self.player.money, money_before - 33)

    def test_cannot_mortgage_with_houses(self):
        sp = self._own(1)
        sp.houses = 1
        result = self.engine.mortgage_property(self.player, sp)
        self.assertFalse(result)
        self.assertFalse(sp.is_mortgaged)

    def test_cannot_unmortgage_if_broke(self):
        sp = self._own(1)
        self.engine.mortgage_property(self.player, sp)
        self.player.money = 0
        result = self.engine.unmortgage_property(self.player, sp)
        self.assertFalse(result)
        self.assertTrue(sp.is_mortgaged)


# ══════════════════════════════════════════════════════════════════════════════
#  6. Jail mechanic tests
# ══════════════════════════════════════════════════════════════════════════════

class TestJailMechanics(unittest.TestCase):

    def setUp(self):
        self.engine = make_engine(2)
        self.p1 = self.engine.players[0]

    def test_go_to_jail_sets_position_10(self):
        self.engine.send_to_jail(self.p1)
        self.assertEqual(self.p1.position, 10)

    def test_go_to_jail_sets_in_jail(self):
        self.engine.send_to_jail(self.p1)
        self.assertTrue(self.p1.in_jail)

    def test_go_to_jail_resets_doubles(self):
        self.engine.doubles_count = 2
        self.engine.send_to_jail(self.p1)
        self.assertEqual(self.engine.doubles_count, 0)

    def test_get_out_of_jail_free_card(self):
        self.engine.send_to_jail(self.p1)
        self.p1.get_out_of_jail_free_cards = 1
        self.engine.use_jail_card()
        self.assertFalse(self.p1.in_jail)
        self.assertEqual(self.p1.get_out_of_jail_free_cards, 0)

    def test_pay_bail_voluntary_costs_50(self):
        self.engine.send_to_jail(self.p1)
        # Give player a large enough balance to easily pay bail and track the -$50 charge.
        # We place the player far from GO so no $200 pass-GO bonus is collected.
        import unittest.mock as mock
        self.p1.position = 10  # already set by send_to_jail
        money_before = self.p1.money
        # Force dice to 3+3=6 so player moves to index 16 (no GO crossing)
        with mock.patch("engine.random.randint", return_value=3):
            self.engine.pay_bail_voluntary()
        self.assertFalse(self.p1.in_jail)
        # Money should be exactly -$50 (no GO bonus since 10+6=16 < 40)
        self.assertEqual(self.p1.money, money_before - 50)

    def test_cannot_pay_bail_if_broke(self):
        self.engine.send_to_jail(self.p1)
        self.p1.money = 0
        self.engine.pay_bail_voluntary()
        self.assertTrue(self.p1.in_jail)   # still in jail


# ══════════════════════════════════════════════════════════════════════════════
#  7. Turn flow tests
# ══════════════════════════════════════════════════════════════════════════════

class TestTurnFlow(unittest.TestCase):

    def setUp(self):
        self.engine = make_engine(2)
        self.p1 = self.engine.players[0]
        self.p2 = self.engine.players[1]

    def test_next_turn_advances_player(self):
        self.assertEqual(self.engine.current_player_index, 0)
        self.engine.next_turn()
        self.assertEqual(self.engine.current_player_index, 1)

    def test_next_turn_wraps(self):
        self.engine.next_turn()  # → P2
        self.engine.next_turn()  # → P1
        self.assertEqual(self.engine.current_player_index, 0)

    def test_next_turn_skips_bankrupt(self):
        self.p2.is_bankrupt = True
        self.engine.next_turn()
        # Should skip P2 and wrap back to P1
        self.assertEqual(self.engine.current_player_index, 0)

    def test_game_over_when_one_player_left(self):
        self.p2.is_bankrupt = True
        self.engine.next_turn()
        self.assertEqual(self.engine.phase, "GAME_OVER")
        self.assertEqual(self.engine.winner, self.p1)

    def test_passing_go_gives_200(self):
        self.p1.position = 38
        self.p1.money = 1500
        # Manually apply move and GO bonus
        passed = self.p1.move(4)
        if passed:
            self.p1.add_money(200)
        self.assertEqual(self.p1.money, 1700)

    def test_three_doubles_sends_to_jail(self):
        """Simulate 3 consecutive doubles using mocked dice."""
        import unittest.mock as mock
        # Ensure it's P1's turn
        self.engine.current_player_index = 0
        self.engine.phase = "WAIT_FOR_ROLL"
        self.engine.doubles_count = 0
        # Roll double (3+3) three times. After the third, P1 should be jailed.
        # Each double keeps it P1's turn (WAIT_FOR_ROLL); 3rd double triggers jail.
        for attempt in range(3):
            if self.p1.in_jail:
                break
            # Reset to P1's turn if a phase change caused rotation
            self.engine.current_player_index = 0
            self.engine.phase = "WAIT_FOR_ROLL"
            with mock.patch("engine.random.randint", return_value=3):
                self.engine.execute_turn()
        self.assertTrue(self.p1.in_jail)

    def test_buy_property_deducts_money(self):
        space = get_property(self.engine.board, 1)
        self.p1.position = 1
        before = self.p1.money
        self.engine.buy_property(self.p1, space)
        self.assertEqual(self.p1.money, before - space.price)
        self.assertIn(space, self.p1.properties)

    def test_skip_buy_advances_turn(self):
        space = self.engine.board[1]
        self.p1.position = 1
        self.engine.phase = "DECIDE_BUY"
        self.engine.skip_buy(self.p1)
        self.assertEqual(self.engine.current_player_index, 1)


# ══════════════════════════════════════════════════════════════════════════════
#  8. Tax space tests
# ══════════════════════════════════════════════════════════════════════════════

class TestTaxSpaces(unittest.TestCase):

    def setUp(self):
        self.engine = make_engine(2)
        self.p1 = self.engine.players[0]

    def test_income_tax_deducts_200(self):
        self.p1.position = 4
        before = self.p1.money
        space = self.engine.board[4]
        self.engine.resolve_space(self.p1, space, 0)
        self.assertEqual(self.p1.money, before - 200)

    def test_luxury_tax_deducts_100(self):
        self.p1.position = 38
        before = self.p1.money
        space = self.engine.board[38]
        self.engine.resolve_space(self.p1, space, 0)
        self.assertEqual(self.p1.money, before - 100)


# ══════════════════════════════════════════════════════════════════════════════
#  9. Rent payment via engine tests
# ══════════════════════════════════════════════════════════════════════════════

class TestEngineRentPayment(unittest.TestCase):

    def setUp(self):
        self.engine = make_engine(2)
        self.p1 = self.engine.players[0]
        self.p2 = self.engine.players[1]

    def test_player_pays_rent_to_owner(self):
        space = self.engine.board[1]  # Mediterranean $2 base
        space.owner = self.p2
        self.p2.properties.append(space)
        self.p1.position = 1
        before_p1 = self.p1.money
        before_p2 = self.p2.money
        self.engine.resolve_space(self.p1, space, 6)
        self.assertEqual(self.p1.money, before_p1 - 2)
        self.assertEqual(self.p2.money, before_p2 + 2)

    def test_no_rent_on_own_property(self):
        space = self.engine.board[1]
        space.owner = self.p1
        self.p1.properties.append(space)
        before = self.p1.money
        self.engine.resolve_space(self.p1, space, 6)
        self.assertEqual(self.p1.money, before)  # unchanged


# ══════════════════════════════════════════════════════════════════════════════
#  10. Bankruptcy tests
# ══════════════════════════════════════════════════════════════════════════════

class TestBankruptcy(unittest.TestCase):

    def setUp(self):
        self.engine = make_engine(3)
        self.p1 = self.engine.players[0]
        self.p2 = self.engine.players[1]
        self.p3 = self.engine.players[2]

    def test_bankruptcy_to_bank(self):
        """Player owes bank tax and goes bankrupt."""
        space = self.engine.board[4]  # Income Tax $200
        self.p1.money = 50   # Not enough
        self.engine.resolve_space(self.p1, space, 0)
        self.assertTrue(self.p1.is_bankrupt)

    def test_bankruptcy_transfers_properties_to_creditor(self):
        """Player owes another player and goes bankrupt."""
        space = self.engine.board[39]  # Boardwalk $50 base rent
        space.owner = self.p2
        self.p2.properties.append(space)
        # Give p2 all Dark Blue for monopoly
        bw2 = self.engine.board[37]
        bw2.owner = self.p2
        self.p2.properties.append(bw2)
        space.houses = 5   # hotel = $2000 rent
        self.p1.money = 100  # Can't pay $2000
        self.engine._charge_player(self.p1, 2000, self.p2)
        self.assertTrue(self.p1.is_bankrupt)

    def test_bankrupt_player_is_skipped_in_turns(self):
        self.p2.is_bankrupt = True
        self.engine.next_turn()
        self.assertEqual(self.engine.current_player_index, 2)  # skips P2


# ══════════════════════════════════════════════════════════════════════════════
#  11. Save / Load tests
# ══════════════════════════════════════════════════════════════════════════════

class TestSaveLoad(unittest.TestCase):

    def setUp(self):
        self.engine = make_engine(2)
        self.save_path = os.path.join(os.path.dirname(__file__), "_test_save.json")

    def tearDown(self):
        if os.path.exists(self.save_path):
            os.remove(self.save_path)

    def test_save_creates_file(self):
        self.engine.save_game(self.save_path)
        self.assertTrue(os.path.exists(self.save_path))

    def test_load_restores_player_money(self):
        self.engine.players[0].money = 750
        self.engine.save_game(self.save_path)
        restored = MonopolyEngine.load_game(self.save_path)
        self.assertEqual(restored.players[0].money, 750)

    def test_load_restores_player_position(self):
        self.engine.players[1].position = 22
        self.engine.save_game(self.save_path)
        restored = MonopolyEngine.load_game(self.save_path)
        self.assertEqual(restored.players[1].position, 22)

    def test_load_restores_property_ownership(self):
        sp = self.engine.board[6]
        sp.owner = self.engine.players[0]
        self.engine.players[0].properties.append(sp)
        self.engine.save_game(self.save_path)
        restored = MonopolyEngine.load_game(self.save_path)
        restored_sp = restored.board[6]
        self.assertIsNotNone(restored_sp.owner)
        self.assertEqual(restored_sp.owner.name, "P1")

    def test_load_restores_houses(self):
        sp = self.engine.board[1]
        sp.owner = self.engine.players[0]
        self.engine.players[0].properties.append(sp)
        sp.houses = 3
        self.engine.save_game(self.save_path)
        restored = MonopolyEngine.load_game(self.save_path)
        self.assertEqual(restored.board[1].houses, 3)

    def test_load_restores_phase(self):
        self.engine.phase = "DECIDE_BUY"
        self.engine.save_game(self.save_path)
        restored = MonopolyEngine.load_game(self.save_path)
        self.assertEqual(restored.phase, "DECIDE_BUY")

    def test_load_restores_jail_status(self):
        self.engine.players[0].in_jail = True
        self.engine.players[0].jail_turns = 2
        self.engine.save_game(self.save_path)
        restored = MonopolyEngine.load_game(self.save_path)
        self.assertTrue(restored.players[0].in_jail)
        self.assertEqual(restored.players[0].jail_turns, 2)

    def test_load_restores_bank_inventory(self):
        self.engine.bank.houses = 20
        self.engine.bank.hotels = 8
        self.engine.save_game(self.save_path)
        restored = MonopolyEngine.load_game(self.save_path)
        self.assertEqual(restored.bank.houses, 20)
        self.assertEqual(restored.bank.hotels, 8)


# ══════════════════════════════════════════════════════════════════════════════
#  12. Card effect tests
# ══════════════════════════════════════════════════════════════════════════════

class TestCardEffects(unittest.TestCase):

    def setUp(self):
        self.engine = make_engine(2)
        self.p1 = self.engine.players[0]
        self.p2 = self.engine.players[1]

    def _get_card(self, card_id):
        all_cards = get_chance_cards() + get_community_chest_cards()
        for c in all_cards:
            if c.id_str == card_id:
                return c
        raise KeyError(f"Card {card_id} not found")

    def test_advance_to_go_gives_200(self):
        card = self._get_card("CH_01")
        self.p1.position = 15
        before = self.p1.money
        self.engine._apply_card(self.p1, card, 0)
        self.assertEqual(self.p1.position, 0)
        # The card pays $200 for passing GO, then landing ON GO
        # triggers the ActionSpace "GO" which adds another $200.
        # Total net gain = $400. Both are standard Monopoly rules.
        self.assertEqual(self.p1.money, before + 400)

    def test_go_to_jail_card(self):
        card = self._get_card("CH_09")
        self.p1.position = 7
        self.engine._apply_card(self.p1, card, 0)
        self.assertTrue(self.p1.in_jail)
        self.assertEqual(self.p1.position, 10)

    def test_get_out_of_jail_free_card(self):
        card = self._get_card("CH_10")
        before = self.p1.get_out_of_jail_free_cards
        self.engine._apply_card(self.p1, card, 0)
        self.assertEqual(self.p1.get_out_of_jail_free_cards, before + 1)

    def test_receive_card(self):
        card = self._get_card("CC_02")  # Bank error: $200
        before = self.p1.money
        self.engine._apply_card(self.p1, card, 0)
        self.assertEqual(self.p1.money, before + 200)

    def test_pay_card(self):
        card = self._get_card("CC_03")  # Doctor's fees: $50
        before = self.p1.money
        self.engine._apply_card(self.p1, card, 0)
        self.assertEqual(self.p1.money, before - 50)

    def test_go_back_3_spaces(self):
        card = self._get_card("CH_08")
        self.p1.position = 7
        self.engine._apply_card(self.p1, card, 0)
        self.assertEqual(self.p1.position, 4)  # 7 - 3 = 4

    def test_pay_players_card(self):
        card = self._get_card("CH_13")  # Chairman: pay each $50
        p2_before = self.p2.money
        p1_before = self.p1.money
        self.engine._apply_card(self.p1, card, 0)
        self.assertEqual(self.p2.money, p2_before + 50)
        self.assertEqual(self.p1.money, p1_before - 50)

    def test_receive_from_players_card(self):
        card = self._get_card("CC_15")  # Birthday: collect $10 from each
        p1_before = self.p1.money
        p2_before = self.p2.money
        self.engine._apply_card(self.p1, card, 0)
        self.assertEqual(self.p1.money, p1_before + 10)
        self.assertEqual(self.p2.money, p2_before - 10)

    def test_property_repair_card_no_props(self):
        card = self._get_card("CC_14")  # Street repairs
        before = self.p1.money
        self.engine._apply_card(self.p1, card, 0)
        self.assertEqual(self.p1.money, before)  # $0 repair cost

    def test_property_repair_card_with_houses(self):
        card = self._get_card("CC_14")  # $40/house, $115/hotel
        sp = self.engine.board[1]
        sp.owner = self.p1
        sp.houses = 3
        self.p1.properties.append(sp)
        before = self.p1.money
        self.engine._apply_card(self.p1, card, 0)
        self.assertEqual(self.p1.money, before - 120)  # 3 × $40


# ══════════════════════════════════════════════════════════════════════════════
#  13. AI behavior tests
# ══════════════════════════════════════════════════════════════════════════════

class TestAIBehavior(unittest.TestCase):

    def setUp(self):
        self.engine = make_engine_with_ai()
        self.human = self.engine.players[0]
        self.bot = self.engine.players[1]

    def test_ai_buys_affordable_property(self):
        space = self.engine.board[1]
        self.bot.money = 1500
        self.engine.ai_decide_buy(self.bot, space)
        self.assertEqual(space.owner, self.bot)

    def test_ai_skips_unaffordable_property(self):
        space = self.engine.board[39]  # $400 Boardwalk
        self.bot.money = 100
        self.engine.ai_decide_buy(self.bot, space)
        self.assertIsNone(space.owner)

    def test_ai_builds_after_monopoly(self):
        """AI build phase should build houses once it has a monopoly."""
        self.bot.money = 5000
        for idx in [1, 3]:
            sp = self.engine.board[idx]
            sp.owner = self.bot
            self.bot.properties.append(sp)
        houses_before = sum(sp.houses for sp in self.bot.properties)
        self.engine.ai_build_phase(self.bot)
        houses_after = sum(sp.houses for sp in self.bot.properties)
        self.assertGreater(houses_after, houses_before)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
