import math

def is_prime(n: int) -> bool:
    """Check if a number is prime."""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def find_goldbach_pair(number: int):
    """
    Find two prime numbers that sum up to the given number.
    Goldbach's conjecture states that every even integer > 2 is the sum of two primes.
    """
    if number <= 2 or number % 2 != 0:
        print("Input must be an even number greater than 2.")
        return

    # Check for pair (i, number-i)
    # We only need to check up to number // 2
    for i in range(2, number // 2 + 1):
        if is_prime(i):
            if is_prime(number - i):
                print(f"Output: {i} + {number - i} = {number}")
                return

    print("No Goldbach pair found (Conjecture disproven?!)")

def main():
    try:
        user_input = input("Enter an even number > 2 to find its Goldbach pair (Enter to quit): ")
        if not user_input:
            return
        
        number = int(user_input)
        find_goldbach_pair(number)
    except ValueError:
        print("Please enter a valid integer.")

if __name__ == "__main__":
    main()