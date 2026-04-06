import re
from itertools import product

def solve_part1(instructions):
    memory = {}
    or_mask = 0
    and_mask = 0
    
    for line in instructions:
        if line.startswith('mask'):
            mask = line.split('=')[1].strip()
            or_mask = int(mask.replace('X', '0'), 2)
            and_mask = int(mask.replace('X', '1'), 2)
        else:
            match = re.match(r'mem\[(\d+)\] = (\d+)', line)
            if match:
                addr = int(match.group(1))
                val = int(match.group(2))
                val = (val | or_mask) & and_mask
                memory[addr] = val
    return sum(memory.values())

def solve_part2(instructions):
    memory = {}
    mask = ""
    
    for line in instructions:
        if line.startswith('mask'):
            mask = line.split('=')[1].strip()
        else:
            match = re.match(r'mem\[(\d+)\] = (\d+)', line)
            if match:
                addr = int(match.group(1))
                val = int(match.group(2))
                
                # Apply 1s from mask (0s unchanged, Xs floating)
                or_mask = int(mask.replace('X', '0'), 2)
                addr |= or_mask
                
                # Identify floating bits
                floating_indices = [35 - i for i, char in enumerate(mask) if char == 'X']
                
                # Clear floating bits in base address to 0
                for i in floating_indices:
                    addr &= ~(1 << i)
                
                # Generate all address combinations
                for bits in product([0, 1], repeat=len(floating_indices)):
                    current_addr = addr
                    for i, bit in enumerate(bits):
                        if bit:
                            current_addr |= (1 << floating_indices[i])
                    memory[current_addr] = val
                    
    return sum(memory.values())

def solve():
    try:
        with open('input-day14.txt', 'r') as f:
            instructions = [line.strip() for line in f]
            
        print(f"Part 1: {solve_part1(instructions)}")
        print(f"Part 2: {solve_part2(instructions)}")
        
    except FileNotFoundError:
        print("Error: input-day14.txt not found.")

if __name__ == '__main__':
    solve()
