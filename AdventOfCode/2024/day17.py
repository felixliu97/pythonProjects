import sys
import re

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            content = f.read()
        
        a_match = re.search(r"Register A: (\d+)", content)
        b_match = re.search(r"Register B: (\d+)", content)
        c_match = re.search(r"Register C: (\d+)", content)
        prog_match = re.search(r"Program: ([\d,]+)", content)
        
        a = int(a_match.group(1)) if a_match else 0
        b = int(b_match.group(1)) if b_match else 0
        c = int(c_match.group(1)) if c_match else 0
        
        program = []
        if prog_match:
            program = list(map(int, prog_match.group(1).split(',')))
            
        return a, b, c, program
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def run_tests():
    print("Running tests...")
    
    # Part 2 Example: 0,3,5,4,3,0 -> A=117440
    ex_prog = [0,3,5,4,3,0]
    found_a_ex = find_lowest_a(ex_prog)
    
    print(f"Test Part 2 Example: Found A = {found_a_ex}")
    expected_a = 117440
    
    if found_a_ex == expected_a:
        print("✅ Part 2 Example Passed (Lowest A matched)")
    else:
        # Check if it reproduces the program at least
        if found_a_ex is not None:
             if verify_part2(found_a_ex, ex_prog):
                  print(f"⚠️ Part 2 Example Mismatch (Expected {expected_a}, Got {found_a_ex}) BUT valid solution.")
             else:
                  print(f"❌ Part 2 Example Failed: Expected {expected_a}, Got {found_a_ex} (Invalid)")
        else:
             print(f"❌ Part 2 Example Failed: Expected {expected_a}, Got None")
             
    print("✅ Tests completed!")

class Computer:
    def __init__(self, a=0, b=0, c=0, program=None):
        self.A = a
        self.B = b
        self.C = c
        self.program = program if program else []
        self.ip = 0
        self.output = []

    def get_combo_value(self, operand):
        if 0 <= operand <= 3:
            return operand
        elif operand == 4:
            return self.A
        elif operand == 5:
            return self.B
        elif operand == 6:
            return self.C
        elif operand == 7:
            raise ValueError("Combo operand 7 is reserved.")
        else:
            raise ValueError(f"Invalid combo operand: {operand}")

    def run_single_step(self):
        # Runs until an output is produced, then returns it.
        # Or returns None if halts.
        while self.ip < len(self.program):
            if self.ip + 1 >= len(self.program):
                return None

            opcode = self.program[self.ip]
            operand = self.program[self.ip + 1]
            instruction_pointer_increased = False

            if opcode == 0: # adv
                denom = 2 ** self.get_combo_value(operand)
                self.A //= denom
            elif opcode == 1: # bxl
                self.B ^= operand
            elif opcode == 2: # bst
                self.B = self.get_combo_value(operand) % 8
            elif opcode == 3: # jnz
                if self.A != 0:
                    self.ip = operand
                    instruction_pointer_increased = True
            elif opcode == 4: # bxc
                self.B ^= self.C
            elif opcode == 5: # out
                val = self.get_combo_value(operand) % 8
                self.ip += 2
                return val
            elif opcode == 6: # bdv
                denom = 2 ** self.get_combo_value(operand)
                self.B = self.A // denom
            elif opcode == 7: # cdv
                denom = 2 ** self.get_combo_value(operand)
                self.C = self.A // denom
            
            if not instruction_pointer_increased:
                self.ip += 2
        return None

    def run(self):
        while True:
            val = self.run_single_step()
            if val is None:
                break
            self.output.append(val)
        return ",".join(map(str, self.output))

def find_lowest_a(program):
    # Backward DFS
    valid_initial_as = []
    
    def dfs(current_a, depth):
        if depth == len(program):
            valid_initial_as.append(current_a)
            return

        target_out = program[-(depth + 1)]
        
        for i in range(8):
            next_a_candidate = (current_a << 3) | i
            
            cpu = Computer(a=next_a_candidate, b=0, c=0, program=program)
            out_val = None
            cpu.ip = 0
            while cpu.ip < len(cpu.program):
                val = cpu.run_single_step() 
                if val is not None:
                    out_val = val
                    break
            
            if out_val == target_out:
                dfs(next_a_candidate, depth + 1)

    dfs(0, 0)
    if valid_initial_as:
        return min(valid_initial_as)
    return None

def verify_part2(a_val, program):
    cpu = Computer(a=a_val, program=program)
    out_str = cpu.run()
    prog_str = ",".join(map(str, program))
    return out_str == prog_str

def solve_part1():
    print("--- Part 1 ---")
    a, b, c, program = parse_input("input-day17.txt")
    cpu = Computer(a, b, c, program)
    result = cpu.run()
    print(f"Result: {result}")

def solve_part2():
    print("--- Part 2 ---")
    # Note: Part 2 assumes program structure allows backward search.
    # We ignore the initial A from input.
    _, _, _, program = parse_input("input-day17.txt")
    lowest_a = find_lowest_a(program)
    print(f"Result: {lowest_a}")
    if lowest_a:
        valid = verify_part2(lowest_a, program)
        print(f"Verification: {valid}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
