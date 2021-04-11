import math

number = int(input('Input: '))
assert(number > 2 and number % 2 == 0)

prime_numbers = []

for num in range(2, number - 1):
    if all(num % i != 0 for i in range(2, int(math.sqrt(num)) + 1)):
        prime_numbers.append(num)

for i in prime_numbers:
    if number - i in prime_numbers:
        print(f"Output: %s + %s = %s" % (i, number - i, number))
        break