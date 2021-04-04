deck1 = [1,1,1,2,2,2,3,3,3,4,4,4,5,5]
deck2 = [1,1,1,1,2,3,4,5,6,7,8,9,9,9]
deck3 = [1,1,1,2,2,3,3,5,5,5,6,6,6,8]
deck4 = [1,1,2,2,3,3,5,5,5,6,6,6,9,9]

def check(deck):
    deck.sort()
    assert(len(deck) == 14)
    cards = {}
    possiblePair = []

    # Put numbers into original dictionary
    for num in deck:
        if num not in cards:
            cards[num] = 1
        else:
            cards[num] += 1

    print(f"Cards:", cards)

    # Find possible pairs
    for key, value in cards.items():
        if value > 1:
            possiblePair.append(key)

    # print(f"Possible Pair:", possiblePair)

    # Iterate through each possible pair
    for pair_card in possiblePair:
        remaining = cards.copy()
        win = True
        remaining[pair_card] -= 2
        if remaining[pair_card] == 0:
            del remaining[pair_card]
        # print(f"Remaining cards:", remaining)
        triplets = []
        # Find 4 triplets
        for i in range(4):
            min_card = min(remaining.keys())
            # print(f"Minimum Key:", min(remaining.keys()))
            if remaining[min_card] >= 3:
                remaining[min_card] -= 3
                triplets.append((min_card, min_card, min_card))
                if remaining[min_card] == 0:
                    del remaining[min_card]
            elif min_card + 1 in remaining.keys() and min_card + 2 in remaining.keys():
                remaining[min_card] -= 1
                remaining[min_card + 1] -= 1
                remaining[min_card + 2] -= 1
                triplets.append((min_card, min_card + 1, min_card + 2))
                if remaining[min_card] == 0:
                    del remaining[min_card]
                if remaining[min_card + 1] == 0:
                    del remaining[min_card + 1]
                if remaining[min_card + 2] == 0:
                    del remaining[min_card + 2]
            else:
                print(f"No Result found in this pair:", pair_card)
                win = False
                break

        if win:
            print(f"This deck wins!")
            print(f"Triplets:", triplets, "Pair:", (pair_card, pair_card))
            break

    if not win:
        print(f"This deck doesn't win.")
        

check(deck4)