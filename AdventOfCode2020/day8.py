def run_instructions(instructions):
    visited = []
    acc, index = 0, 0
    while index < len(instructions) and index not in visited:
        instruction = instructions[index]
        operation = instruction[:3]
        symbol = instruction[4]
        number = int(instruction[5:])
        visited.append(index)
        if operation != 'jmp':
            index += 1
            if operation == 'acc':
                acc = acc + number if symbol == '+' else acc - number
        else:
            index = index + number if symbol == '+' else index - number
    success = True if index >= len(instructions) - 1 else False
    return(visited, success, acc)

def fix_instructions(instructions):
    visited, success, acc = run_instructions(instructions)
    if success:
        print(acc)
        return acc
    for index in visited:
        if(instructions[index][:3] in ('jmp','nop')):
            new_instructions = instructions[:]
            new_instructions[index] = 'nop' + instructions[index][3:] if instructions[index][:3] == 'jmp' else 'jmp' + instructions[index][3:]
            visited, success, acc = run_instructions(new_instructions)
            if success:
                print(f'Success run, final accumulator:', acc)
                break

with open('input-day8.txt', 'r') as f:
    instructions = [line.replace('\n','') for line in f.readlines()]
    visited, success, acc = run_instructions(instructions)
    if not success:
        print(f'Program stuck, accumulator:', acc)
    else:
        print(f'Success run, final accumulator:', acc)
    fix_instructions(instructions)