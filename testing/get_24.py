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
                f'({a} {op1} {b}) {op2} {c} {op3} {d}',
                f'{a} {op1} ({b} {op2} {c}) {op3} {d}',
                f'{a} {op1} {b} {op2} ({c} {op3} {d})',
                f'({a} {op1} {b} {op2} {c}) {op3} {d}',
                f'{a} {op1} ({b} {op2} {c} {op3} {d})'
            ]

            for expr in expressions:
                try:
                    if eval(expr) == 24:
                        solutions.append(expr)
                except ZeroDivisionError:
                    pass

    return solutions

nums = [1,4,5,6]
solutions = get_24_solution(nums)
print(f"solutions for {nums}")
print(solutions)
