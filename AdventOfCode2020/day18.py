def find_open_parenthesis(expression):
    return(expression.find('('))

def find_close_parenthesis(expression):
    return(expression.find(')'))

def calculate(expression, mode):
    if mode == 'left_first':
        result = int(expression.pop(0))
        while expression:
            op = expression.pop(0)
            num = int(expression.pop(0))
            if op == '+':
                result += num
            elif op == '*':
                result *= num
    else:
        result = 1
        op = ' '.join(expression).split(' * ')
        for o in op:
            nums = [int(x) for x in o.split(' + ')]
            result *= sum(nums)
    return result

def calculate_parenthesis(expression, mode):
    open_index = find_open_parenthesis(expression)
    close_index = find_close_parenthesis(expression)
    if open_index != -1:
        prev, next = open_index, open_index
        while open_index < close_index and next != -1:
            next = find_open_parenthesis(expression[open_index+1:close_index])
            if next != -1:
                next += 1
            open_index = open_index + next
            prev = open_index
        sub_exp = expression[prev+1:close_index+1]
        sub = sub_exp.strip('(').strip(')').split()
        result = calculate(sub, mode)
        return expression[:prev+1] + str(result) + expression[close_index+1:]

with open('input-day18.txt', 'r') as f:
    expressions = [line.strip() for line in f.readlines()]
    result1 = []
    result2 = []
    for expression in expressions:
        expression1, expression2 = expression, expression
        while find_open_parenthesis(expression1) != -1:
            expression1 = calculate_parenthesis(expression1, 'left_first')
        result1.append(calculate(expression1.strip('(').strip(')').split(), 'left_first'))
        while find_open_parenthesis(expression2) != -1:
            expression2 = calculate_parenthesis(expression2, 'addition_first')
        result2.append(calculate(expression2.strip('(').strip(')').split(), 'addition_first'))

    print(f'part 1:', sum(result1))
    print(f'part 2:', sum(result2))