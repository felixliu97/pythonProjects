def rule1(deck1, deck2):
    while deck1 and deck2:
        card1 = deck1.pop(0)
        card2 = deck2.pop(0)
        if card1 > card2:
            winning_deck = deck1
            deck1.append(card1)
            deck1.append(card2)
        else:
            winning_deck = deck2
            deck2.append(card2)
            deck2.append(card1)

    return (deck1, deck2)


def rule2(deck1, deck2):
    #need to reset history in each subgame
    history = []
    while deck1 and deck2:
        if (deck1, 1) in history or (deck2, 2) in history:
            return deck1, deck2, 1

        history.append((deck1[:], 1))
        history.append((deck2[:], 2))
        card1 = deck1.pop(0)
        card2 = deck2.pop(0)

        if card1 <= len(deck1) and card2 <= len(deck2):
            #determine subgame winner
            _, _, winner = rule2(deck1[:card1], deck2[:card2])
            if winner == 1:
                deck1.append(card1)
                deck1.append(card2)
            else:
                deck2.append(card2)
                deck2.append(card1)
        elif card1 > card2:
            deck1.append(card1)
            deck1.append(card2)
        else:
            deck2.append(card2)
            deck2.append(card1)
    return deck1, deck2, 1 if deck1 else 2


with open('input-day22.txt', 'r') as f:
    player1, player2 = f.read().strip().split('\n\n')
    deck1 = [int(x) for x in player1.split('\n') if x != 'Player 1:']
    deck2 = [int(x) for x in player2.split('\n') if x != 'Player 2:']

    copy1_1, copy1_2, copy2_1, copy2_2 = deck1[:], deck2[:], deck1[:], deck2[:]

    rule1_deck1, rule1_deck2 = rule1(copy1_1, copy1_2)
    score = 0
    winning_deck = rule1_deck1 if len(rule1_deck1) > 0 else rule1_deck2
    multiplier = len(winning_deck)
    for card in winning_deck:
        score += card * multiplier
        multiplier -= 1
    print(f'part 1 result:', score)

    history = []
    rule2_deck1, rule2_deck2, winner = rule2(copy2_1, copy2_2)

    score = 0
    winning_deck = rule2_deck1 if winner == 1 else rule2_deck2
    multiplier = len(winning_deck)
    for card in winning_deck:
        score += card * multiplier
        multiplier -= 1
    print(f'part 2 result:', score)