import re

# part1
def get_number(input):
    first_match = re.search(r'\d', input)
    first_digit = first_match.group() if first_match else None

    match_last = re.search(r'\d', input[::-1])
    last_digit = match_last.group() if match_last else None

    return int(first_digit+last_digit)

# part2
def get_replaced_number(input):
    word_to_number = {
        'one': '1',
        'two': '2',
        'three': '3',
        'four': '4',
        'five': '5',
        'six': '6',
        'seven': '7',
        'eight': '8',
        'nine': '9',
    }

    first_match = re.search(r'(?:' + '|'.join(map(re.escape, word_to_number.keys())) + r')|\d', input)
    first_match_value = first_match.group() if first_match else None
    first_digit = word_to_number.get(first_match_value, first_match_value) if first_match_value else None

    reversed_word_to_number = {word[::-1]: value for word, value in word_to_number.items()}
    last_match = re.search(r'(?:' + '|'.join(map(re.escape, reversed_word_to_number.keys())) + r')|\d',input[::-1])
    last_match_value = last_match.group() if last_match else None
    last_digit = reversed_word_to_number.get(last_match_value, last_match_value) if last_match_value else None

    return int(first_digit+last_digit)

sum1, sum2 = 0, 0
file = open('input-day1.txt', 'r')
lines = file.readlines()
for line in lines:
    num = get_number(line)
    sum1 += num
    num2 = get_replaced_number(line)
    sum2 += num2

print(f"part1:{sum1}")
print(f"part2:{sum2}")