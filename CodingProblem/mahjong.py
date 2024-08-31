from collections import Counter
import unittest

# Check if tile is valid
def is_valid_tile(tile):
    if not ((len(tile) == 2) and tile[0].isdigit() and (0 <= int(tile[0]) <= 9) and tile[1] in ['万', '筒', '条']):
        print(f"{tile} is not a valid tile")
        return False
    return True

def add_tile(tile, increment:int):
    number, category = list(tile)
    return f"{int(number)+increment}{category}"
# Check if the set of tiles win
def is_winning_hand(tiles):
    if len(tiles) != 14:
        print(f"Got {len(tiles)} tiles which is not equal to 14")
        return False, None, None
    
    for tile in tiles:
        if not is_valid_tile(tile):
            return False, None, None

    tile_counts = Counter(tiles)
    print(f"tile_counts:{tile_counts}")
    
    # Check pairs
    for tile, count in tile_counts.items():
        if count >= 2:
            pair = tile
            triplets = []
            # Create a copy of original tiles
            remaining = tile_counts.copy()
            win = True
            remaining[tile] -= 2
            if remaining[tile] == 0:
                del remaining[tile]
            print(f"Trying 2*({tile}) as pair")
            # Check if remaining tiles are 4 triplets
            for _ in range(4):
                # Find minimum tile and try to remove 1 triplet from remaining
                min_tile = min(remaining.keys())
                # If has 3 or more same tile
                if remaining[min_tile] >= 3:
                    remaining[min_tile] -= 3
                    triplets.append((min_tile, min_tile, min_tile))
                    if remaining[min_tile] == 0:
                        del remaining[min_tile]
                # If less than 3 of same tiles, but next 2 adjacent tiles
                elif add_tile(min_tile,1) in remaining.keys() and add_tile(min_tile,2) in remaining.keys():
                    remaining[min_tile] -= 1
                    remaining[add_tile(min_tile,1)] -= 1
                    remaining[add_tile(min_tile,2)] -= 1
                    triplets.append((min_tile, add_tile(min_tile,1), add_tile(min_tile,2)))
                    if remaining[min_tile] == 0:
                        del remaining[min_tile]
                    if remaining[add_tile(min_tile,1)] == 0:
                        del remaining[add_tile(min_tile,1)]
                    if remaining[add_tile(min_tile,2)] == 0:
                        del remaining[add_tile(min_tile,2)]
                # Can not find triplet
                else:
                    print(f"\033[33mThis pair doesn't win!\033[0m")
                    win = False
                    break
    if win:
        print(f"\033[32mThis pair wins! Pair:{pair}, triplets:{triplets}!\033[0m")
        return True, pair, triplets
    else:
        return False, None, None

class TestMahjongWinningHand(unittest.TestCase):
    def test_add_tile_1(self):
        tile = "1万"
        assert(add_tile(tile, 1) == "2万")
    def test_winning_hand_1(self):
        tiles = ["1万", "1万", "1万", "2筒", "3筒", "4筒", "5条", "6条", "7条", "9万", "9万", "9万", "1筒", "1筒"]
        result, pair, combinations = is_winning_hand(tiles)
        self.assertTrue(result)
        self.assertEqual(pair, "1筒")
        self.assertEqual(len(combinations), 4)

    def test_winning_hand_2(self):
        tiles = ["1万", "2万", "3万", "2筒", "3筒", "4筒", "5条", "6条", "7条", "7万", "8万", "9万", "1筒", "1筒"]
        result, pair, combinations = is_winning_hand(tiles)
        self.assertTrue(result)
        self.assertEqual(pair, "1筒")
        self.assertEqual(len(combinations), 4)

    def test_not_winning_hand_1(self):
        tiles = ["1万", "1万", "1万", "2筒", "3筒", "4筒", "5条", "6条", "7条", "9万", "9万", "9万", "1筒", "2筒"]
        result, pair, combinations = is_winning_hand(tiles)
        self.assertFalse(result)

    def test_invalid_hand_size(self):
        tiles = ["1万", "1万", "1万", "2筒", "3筒", "4筒", "5条", "6条", "7条", "9万", "9万", "9万", "1筒"]
        result, pair, combinations = is_winning_hand(tiles)
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()