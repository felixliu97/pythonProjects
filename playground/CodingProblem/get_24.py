import argparse
import unittest
import sys
from itertools import permutations, product

def get_24_solution(nums):
    if len(nums) != 4:
        raise ValueError("Input must be exactly 4 numbers")
        
    for n in nums:
        if not (1 <= n <= 13):
            raise ValueError("Numbers must be between 1 and 13")
            
    solutions = []
    ops = ['+', '-', '*', '/']
    
    # Try all permutations of numbers
    for perm in permutations(nums):
        # Try all combinations of 3 operators
        for op_perm in product(ops, repeat=3):
            a, b, c, d = perm
            op1, op2, op3 = op_perm

            # There are exactly 5 distinct binary tree shapes for 4 leaves.
            # We construct explicit parenthesized strings for each.
            expressions = [
                # 1. ((A op1 B) op2 C) op3 D
                f"(({a} {op1} {b}) {op2} {c}) {op3} {d}",
                # 2. (A op1 (B op2 C)) op3 D
                f"({a} {op1} ({b} {op2} {c})) {op3} {d}",
                # 3. (A op1 B) op2 (C op3 D)
                f"({a} {op1} {b}) {op2} ({c} {op3} {d})",
                # 4. A op1 ((B op2 C) op3 D)
                f"{a} {op1} (({b} {op2} {c}) {op3} {d})",
                # 5. A op1 (B op2 (C op3 D))
                f"{a} {op1} ({b} {op2} ({c} {op3} {d}))"
            ]

            for expr in expressions:
                try:
                    # Evaluate the expression
                    val = eval(expr)
                    # Check if close to 24 (float point precision)
                    if abs(24 - val) < 1e-6:
                        # Normalize solution string if needed, or just keep explicit
                        if expr not in solutions:
                            solutions.append(expr)
                except ZeroDivisionError:
                    pass
                except Exception:
                    pass

    return sorted(list(set(solutions))) # Unique solutions

def main():
    # Check if --test is passed
    if '--test' in sys.argv:
        sys.argv.remove('--test') # Remove to not confuse unittest
        # Use verbosity=0 to suppress dots/test names, so only our colored output shows (plus summary)
        unittest.main(verbosity=0)
        return

    parser = argparse.ArgumentParser(description="Find operations to make 24 from 4 numbers.")
    parser.add_argument('numbers', metavar='N', type=float, nargs=4,
                        help='Four numbers to use (1-13)')
    
    args = parser.parse_args()
    
    # Convert to int if they are integers for cleaner display, else keep float
    cleaned_nums = []
    for n in args.numbers:
        if not n.is_integer():
             print("Error: All numbers must be integers.")
             return
        cleaned_nums.append(int(n))
            
    print(f"Solving for: {cleaned_nums}")
    try:
        solutions = get_24_solution(cleaned_nums)
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    if solutions:
        print(f"Found {len(solutions)} solutions:")
        for sol in solutions:
            print(sol)
    else:
        print("No solutions found.")

class TestGet24(unittest.TestCase):
    def print_result(self, nums, solutions):
        GREEN = '\033[92m'
        RED = '\033[91m'
        RESET = '\033[0m'
        
        if solutions:
            print(f"{GREEN}Solution for {nums}: {solutions[0]}{RESET}")
        else:
            print(f"{RED}No solution for {nums}{RESET}")

    def test_solvable_standard(self):
        # 4, 1, 8, 7 -> (8-7+1)*4 = 8? No. (8-4)*(7-1) = 24.
        nums = [4, 1, 8, 7]
        solutions = get_24_solution(nums)
        self.print_result(nums, solutions)
        self.assertTrue(len(solutions) > 0)
        val = eval(solutions[0])
        self.assertAlmostEqual(val, 24, delta=1e-6)

    def test_solvable_fractional(self):
        # 8 8 3 3 -> 8 / (3 - 8/3)
        nums = [8, 8, 3, 3]
        solutions = get_24_solution(nums)
        self.print_result(nums, solutions)
        self.assertTrue(len(solutions) > 0)
        
    def test_unsolvable(self):
        # 1 1 1 1 -> Max 4
        nums = [1, 1, 1, 1]
        solutions = get_24_solution(nums)
        self.print_result(nums, solutions)
        self.assertEqual(len(solutions), 0)

    # New Test Cases
    def test_all_sixes(self):
        # 6 6 6 6 -> 6+6+6+6
        nums = [6, 6, 6, 6]
        solutions = get_24_solution(nums)
        self.print_result(nums, solutions)
        self.assertTrue(len(solutions) > 0)

    def test_one_two_three_four(self):
        # 1 2 3 4 -> 1*2*3*4
        nums = [1, 2, 3, 4]
        solutions = get_24_solution(nums)
        self.print_result(nums, solutions)
        self.assertTrue(len(solutions) > 0)
    
    def test_fraction_hard_5551(self):
        # 5 5 5 1 -> 5 * (5 - 1/5)
        nums = [5, 5, 5, 1]
        solutions = get_24_solution(nums)
        self.print_result(nums, solutions)
        self.assertTrue(len(solutions) > 0)

    def test_fraction_hard_3377(self):
         # 3 3 7 7 -> (3 + 3/7) * 7
         nums = [3, 3, 7, 7]
         solutions = get_24_solution(nums)
         self.print_result(nums, solutions)
         self.assertTrue(len(solutions) > 0)

    def test_large_numbers_10_10_4_4(self):
         # 10 10 4 4 -> (10 * 10 - 4) / 4
         nums = [10, 10, 4, 4]
         solutions = get_24_solution(nums)
         self.print_result(nums, solutions)
         self.assertTrue(len(solutions) > 0)

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            get_24_solution([1, 2, 3]) # Wrong length
        
        with self.assertRaisesRegex(ValueError, "between 1 and 13"):
             get_24_solution([14, 1, 1, 1])
             
        with self.assertRaisesRegex(ValueError, "between 1 and 13"):
             get_24_solution([0, 5, 5, 5])

if __name__ == "__main__":
    main()