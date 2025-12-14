import sys
import re

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def parse_game(line):
    # Game 1: 3 blue, 4 red; 1 red, 2 green, 6 blue; 2 green
    parts = line.split(':')
    game_id = int(parts[0].split()[1])
    
    rounds = parts[1].split(';')
    parsed_rounds = []
    
    for r in rounds:
        cubes = r.split(',')
        round_data = {'red': 0, 'green': 0, 'blue': 0}
        for c in cubes:
            c = c.strip()
            count, color = c.split()
            round_data[color] = int(count)
        parsed_rounds.append(round_data)
        
    return game_id, parsed_rounds

def run_tests():
    print("Running tests...")
    
    example = """Game 1: 3 blue, 4 red; 1 red, 2 green, 6 blue; 2 green
Game 2: 1 blue, 2 green; 3 green, 4 blue, 1 red; 1 green, 1 blue
Game 3: 8 green, 6 blue, 20 red; 5 blue, 4 red, 13 green; 5 green, 1 red
Game 4: 1 green, 3 red, 6 blue; 3 green, 6 red; 3 green, 15 blue, 14 red
Game 5: 6 red, 1 blue, 3 green; 2 blue, 1 red, 2 green"""
    
    lines = example.split('\n')
    
    # Part 1 logic
    possible_sum = 0
    limits = {'red': 12, 'green': 13, 'blue': 14}
    
    for line in lines:
        game_id, rounds = parse_game(line)
        possible = True
        for r in rounds:
            if r['red'] > limits['red'] or r['green'] > limits['green'] or r['blue'] > limits['blue']:
                possible = False
                break
        if possible:
            possible_sum += game_id
            
    expected_p1 = 8
    if possible_sum == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {possible_sum}")

    # Part 2 logic
    power_sum = 0
    for line in lines:
        game_id, rounds = parse_game(line)
        min_cubes = {'red': 0, 'green': 0, 'blue': 0}
        for r in rounds:
            min_cubes['red'] = max(min_cubes['red'], r['red'])
            min_cubes['green'] = max(min_cubes['green'], r['green'])
            min_cubes['blue'] = max(min_cubes['blue'], r['blue'])
        
        power = min_cubes['red'] * min_cubes['green'] * min_cubes['blue']
        power_sum += power
        
    expected_p2 = 2286
    if power_sum == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {power_sum}")

    print("✅ Tests completed!")

def solve_part1():
    print("--- Part 1 ---")
    data = parse_input("2023-day2.txt")
    lines = data.split('\n')
    possible_sum = 0
    limits = {'red': 12, 'green': 13, 'blue': 14}
    
    for line in lines:
        game_id, rounds = parse_game(line)
        possible = True
        for r in rounds:
            if r['red'] > limits['red'] or r['green'] > limits['green'] or r['blue'] > limits['blue']:
                possible = False
                break
        if possible:
            possible_sum += game_id
    print(f"Result: {possible_sum}")

def solve_part2():
    print("--- Part 2 ---")
    data = parse_input("2023-day2.txt")
    lines = data.split('\n')
    power_sum = 0
    for line in lines:
        game_id, rounds = parse_game(line)
        min_cubes = {'red': 0, 'green': 0, 'blue': 0}
        for r in rounds:
            min_cubes['red'] = max(min_cubes['red'], r['red'])
            min_cubes['green'] = max(min_cubes['green'], r['green'])
            min_cubes['blue'] = max(min_cubes['blue'], r['blue'])
        
        power = min_cubes['red'] * min_cubes['green'] * min_cubes['blue']
        power_sum += power
    print(f"Result: {power_sum}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
