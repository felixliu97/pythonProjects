from collections import Counter
import unittest
import sys

# Constants for tile categories
CATEGORIES = ['万', '筒', '条']

def is_valid_tile(tile: str) -> bool:
    """Check if a tile string is valid (e.g. '1万')."""
    if len(tile) != 2:
        return False
    number, category = tile[0], tile[1]
    return number.isdigit() and '1' <= number <= '9' and category in CATEGORIES

def get_next_tile(tile: str, steps: int = 1) -> str:
    """Return the next tile in sequence (e.g. 1万 -> 2万). Returns None if invalid."""
    try:
        if not is_valid_tile(tile):
            return None
        num = int(tile[0])
        category = tile[1]
        new_num = num + steps
        if new_num > 9:
            return None
        return f"{new_num}{category}"
    except Exception:
        return None

def can_form_sets(tile_counts: Counter, sets_needed: int) -> tuple[bool, list]:
    """
    Recursively check if the tiles can form 'sets_needed' valid sets (triplets or sequences).
    Returns (True, list_of_sets) if possible, else (False, None).
    """
    if sets_needed == 0:
        return True, []
    
    # Get the smallest tile to enforce order and avoid redundant checks
    # (Keys in Counter are not ordered, but sorting keys helps deterministic processing)
    if not tile_counts:
        return False, None
    
    sorted_tiles = sorted(tile_counts.keys())
    first_tile = sorted_tiles[0] 
    
    # Try to form a Triplet (AAA)
    if tile_counts[first_tile] >= 3:
        new_counts = tile_counts.copy()
        new_counts[first_tile] -= 3
        if new_counts[first_tile] == 0:
            del new_counts[first_tile]
            
        success, res_sets = can_form_sets(new_counts, sets_needed - 1)
        if success:
            return True, [(first_tile, first_tile, first_tile)] + res_sets

    # Try to form a Sequence (ABC)
    t2 = get_next_tile(first_tile, 1)
    t3 = get_next_tile(first_tile, 2)
    
    if t2 and t3 and tile_counts[t2] > 0 and tile_counts[t3] > 0:
        new_counts = tile_counts.copy()
        new_counts[first_tile] -= 1
        new_counts[t2] -= 1
        new_counts[t3] -= 1
        
        # Clean up zero counts
        for t in [first_tile, t2, t3]:
            if new_counts[t] == 0:
                del new_counts[t]
                
        success, res_sets = can_form_sets(new_counts, sets_needed - 1)
        if success:
            return True, [(first_tile, t2, t3)] + res_sets
            
    return False, None

def is_winning_hand(tiles: list[str]) -> tuple[bool, str, list]:
    """
    Check if the list of 14 tiles forms a winning hand (pair + 4 sets).
    Returns (is_win, pair_tile, sets_list).
    """
    if len(tiles) != 14:
        # print(f"Invalid tile count: {len(tiles)}")
        return False, None, None
        
    for tile in tiles:
        if not is_valid_tile(tile):
            # print(f"Invalid tile found: {tile}")
            return False, None, None

    counts = Counter(tiles)
    
    # Iterate through each unique tile to see if it can be the 'Pair'
    for potential_pair in counts.keys():
        if counts[potential_pair] >= 2:
            remaining_counts = counts.copy()
            remaining_counts[potential_pair] -= 2
            if remaining_counts[potential_pair] == 0:
                del remaining_counts[potential_pair]
            
            # Check if the remaining 12 tiles can form 4 sets
            success, winning_sets = can_form_sets(remaining_counts, 4)
            if success:
                return True, potential_pair, winning_sets

    return False, None, None


class CustomTestResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        self.stream.write(f"\n✅ {test.shortDescription() or str(test)}")
        self.stream.flush()

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.stream.write(f"\n❌ {test.shortDescription() or str(test)}")
        self.stream.flush()

    def addError(self, test, err):
        super().addError(test, err)
        self.stream.write(f"\n❓ {test.shortDescription() or str(test)} (Error)")
        self.stream.flush()

class CustomTestRunner(unittest.TextTestRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resultclass = CustomTestResult

class TestMahjongWinningHand(unittest.TestCase):
    def test_add_tile_1(self):
        """Test getting the next tile in sequence (e.g. 1万 -> 2万)."""
        print(f"   Testing next tile logic: 1万 + 1")
        self.assertEqual(get_next_tile("1万", 1), "2万")
        print(f"   Testing invalid next tile logic: 9万 + 1")
        self.assertIsNone(get_next_tile("9万", 1))

    def test_winning_hand_simple(self):
        """Test a clear standard winning hand."""
        tiles = ["1万", "1万", "1万", "2筒", "3筒", "4筒", "5条", "6条", "7条", "9万", "9万", "9万", "1筒", "1筒"]
        print(f"   Testing Hand: {tiles}")
        result, pair, combinations = is_winning_hand(tiles)
        self.assertTrue(result)
        self.assertEqual(pair, "1筒")
        self.assertEqual(len(combinations), 4)

    def test_winning_hand_mixed(self):
        """Test a mixed winning hand with runs and triplets."""
        tiles = ["1万", "2万", "3万", "2筒", "3筒", "4筒", "5条", "6条", "7条", "7万", "8万", "9万", "1筒", "1筒"]
        print(f"   Testing Hand: {tiles}")
        result, pair, combinations = is_winning_hand(tiles)
        self.assertTrue(result)
        self.assertEqual(pair, "1筒")
        self.assertEqual(len(combinations), 4)

    def test_not_winning_hand(self):
        """Test a hand that is NOT a winning hand (invalid mix)."""
        tiles = ["1万", "1万", "1万", "2筒", "3筒", "4筒", "5条", "6条", "7条", "9万", "9万", "9万", "1筒", "2筒"]
        print(f"   Testing Hand: {tiles}")
        result, _, _ = is_winning_hand(tiles)
        self.assertFalse(result)

    def test_complex_chu_lian_subset(self):
        """Test a complex hand combining similar sequences (Pure Triplets vs Sequences check)."""
        # A complex hand that might fail greedy approach: 1112345678999 + pair
        # Let's try 222 34 345 ... 
        # Case: 234 234 vs 22 33 44
        tiles = ["2万", "2万", "2万", "3万", "3万", "3万", "4万", "4万", "4万", "5万", "5万", "5万", "9筒", "9筒"]
        print(f"   Testing Hand: {tiles}")
        result, pair, combs = is_winning_hand(tiles)
        self.assertTrue(result)
        self.assertEqual(pair, "9筒")

if __name__ == "__main__":
    runner = CustomTestRunner(verbosity=2)
    unittest.main(testRunner=runner)