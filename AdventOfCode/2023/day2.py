import re

def validate_game(game, red, green, blue):
    game_id, subsets = game.split(':')
    game_id = int(game_id.strip('Game '))
    for subset in subsets.split(';'):
        for color in subset.split(','):
            color = color.strip()
            num = int(re.search(r'\d+', color).group())
            if color.endswith('red') and num > red:
                return game_id, False
            elif color.endswith('green') and num > green:
                return game_id, False
            elif color.endswith('blue') and num > blue:
                return game_id, False
    
    return game_id, True

def power_of_colors(game):
    max_red, max_green, max_blue = 0, 0 , 0
    _, subsets = game.split(':')
    for subset in subsets.split(';'):
        for color in subset.split(','):
            color = color.strip()
            num = int(re.search(r'\d+', color).group())
            if color.endswith('red'):
                max_red = max(num, max_red)
            elif color.endswith('green'):
                max_green = max(num, max_green)
            elif color.endswith('blue'):
                max_blue = max(num, max_blue)
    
    return max_red*max_green*max_blue


file = open('input-day2.txt', 'r')
lines = file.readlines()
games = []
power_sum = 0
for line in lines:
    game_id, valid = validate_game(line, red=12, green=13, blue=14)
    if valid:
        games.append(game_id)
    power_sum += power_of_colors(line)

print(f"part1:{sum(games)}")
print(f"part2:{power_sum}")