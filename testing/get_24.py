from itertools import permutations, product

def get_24_solution(nums):
    solutions = []
    ops = ['+', '-', '*', '/']
    for perm in permutations(nums):
        for op_perm in product(ops, repeat=3):
            a, b, c, d = perm
            op1, op2, op3 = op_perm

            # Try all possible placements of parentheses
            expressions = [
                f"({a} {op1} {b}) {op2} {c} {op3} {d}",
                f"{a} {op1} ({b} {op2} {c}) {op3} {d}",
                f"{a} {op1} {b} {op2} ({c} {op3} {d})",
                f"({a} {op1} {b} {op2} {c}) {op3} {d}",
                f"{a} {op1} ({b} {op2} {c} {op3} {d})",
                f"({a} {op1} {b}) {op2} ({c} {op3} {d})"
            ]

            for expr in expressions:
                try:
                    if abs(24 - eval(expr)) < 1e-6:
                        if expr not in solutions:
                            solutions.append(expr)
                except ZeroDivisionError:
                    pass

    return solutions

def main():
    try:
        input_numbers = [int(x) for x in input("Enter four numbers separated by spaces: ").split()]
        if len(input_numbers) != 4:
            print("Please enter exactly four numbers.")
        else:
            solutions = get_24_solution(input_numbers)
            if solutions:
                print("Solutions to calculate 24:")
                for solution in solutions:
                    print(solution)
            else:
                print("No solutions found to calculate 24.")
    except ValueError:
        print("Invalid input. Please enter valid numbers separated by spaces.")


if __name__ == "__main__":
    main()