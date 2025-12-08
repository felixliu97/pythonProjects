import re

def find_lowest_a(program):
    # Backward DFS
    # depth 0 corresponds to the LAST output (index -1)
    # We want to find an 'a' that generates program[-(depth+1)] as the first output
    # given that the next state of 'a' will be 'current_a'.
    # Because A usually shifts by 3 bits each iteration (adv 3),
    # prev_a ~ current_a << 3
    
    valid_initial_as = []
    
    def dfs(current_a, depth):
        if depth == len(program):
            valid_initial_as.append(current_a)
            return

        target_out = program[-(depth + 1)]
        
        # Try all possible 3-bit values for the "current" lowest 3 bits
        # The equation is generally: a_next = a_prev >> 3
        # So a_prev = (a_next << 3) + i
        for i in range(8):
            next_a_candidate = (current_a << 3) | i
            
            # Simulate ONE output step with this candidate A
            # We assume B and C start at 0 for each *new* run from scratch, 
            # OR that they are reset effectively by the loop body.
            # In the input program, B and C are typically derived from A.
            
            # Create a snippet computer just to get the first output
            # We use the FULL program logic but stop after one output.
            
            # However, looking at the input program structure is safer.
            # Program: 2,4, 1,3, 7,5, 4,7, 0,3, 1,5, 5,5, 3,0
            # 2,4: bst A (B = A % 8)
            # 1,3: bxl 3 (B = B ^ 3)
            # 7,5: cdv B (C = A >> B)
            # 4,7: bxc   (B = B ^ C)
            # 0,3: adv 3 (A = A >> 3)
            # 1,5: bxl 5 (B = B ^ 5)
            # 5,5: out B
            # 3,0: jnz 0
            
            # The loop creates B and C from A, outputs B, then shifts A. 
            # B and C don't carry over loop iterations in a meaningful way 
            # that depends on previous iterations (they are blindly overwritten).
            # So checking "output one value" is correct.
            
            cpu = Computer(a=next_a_candidate, b=0, c=0, program=program)
            
            # Run until first output
            out_val = None
            cpu.ip = 0
            while cpu.ip < len(cpu.program):
                 # Manually stepping to catch the first output
                 # Or just run and check the first element of output
                 # But running the whole thing might be infinite if we don't handle the jump carefully?
                 # Actually, for checking, we can just run the full program simulation
                 # provided it terminates. 
                 # But we only care about the *first* output matching *target_out*
                 # AND that the *next* state of A matches *current_a* (which is implicitly true by construction if adv 3 is used).
                 
                 # Optimization: Run *exactly one iteration* of the loop manually or check full output?
                 # running full output is costly if A is large.
                 # Let's just run until `len(cpu.output) == 1`.
                 
                val = cpu.run_single_step() 
                if val is not None:
                    out_val = val
                    break
            
            if out_val == target_out:
                # Also, we implicitly assume A becomes `current_a` after this loop.
                # Let's verify that A_next is indeed `current_a` (or close enough if the shift isn't exactly 3? Input says adv 3).
                # If adv 3 is hardcoded, it is guaranteed.
                # Let's verify A state just in case.
                
                # Wait, cpu.run_single_step() consumes the state.
                # If the loop ends with 3,0 (jnz), and we stopped at output...
                # The 'adv 3' happens at specific points.
                # In the example input: adv 3 (0,3) happens BEFORE output? 
                # No, standard is usually calculation -> output -> shift -> jump or calc -> shift -> output -> jump?
                # Input: ... 0,3 (adv 3) ... 5,5 (out) ... 3,0 (jump).
                # Wait, order matters.
                # My input: 2,4, 1,3, 7,5, 4,7, 0,3 (adv3), 1,5, 5,5(out), 3,0.
                # So A is shifted BEFORE output?
                # If A is shifted before output, then `out A%8` uses the SHIFTED A?
                # No, output is `5,5` -> `out B`. B is derived from unshifted A.
                # So the order:
                # 1. B, C derived from A.
                # 2. A shifted (A = A >> 3).
                # 3. B modified more.
                # 4. Out B.
                # 5. Jump.
                
                # So the A that produces the NEXT iteration is indeed `current_a`.
                # And the A that produces THIS iteration is `next_a_candidate`.
                # We just need to check if `next_a_candidate` produces `target_out`.
                
                dfs(next_a_candidate, depth + 1)

    dfs(0, 0)
    if valid_initial_as:
        return min(valid_initial_as)
    return None

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

def verify_part2(a_val, program):
    cpu = Computer(a=a_val, program=program)
    out_str = cpu.run()
    prog_str = ",".join(map(str, program))
    return out_str == prog_str

def parse_input(filename):
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

def solve():
    print("--- Verification ---")
    
    print("\n--- Real Input ---")
    a, b, c, program = parse_input('input-day17.txt')
    cpu = Computer(a, b, c, program)
    result = cpu.run()
    print(f"Part 1 Output: {result}")
    
    print("\n--- Part 2 ---")
    # Part 2 Example: 0,3,5,4,3,0 -> A=117440
    ex_prog = [0,3,5,4,3,0]
    found_a_ex = find_lowest_a(ex_prog)
    print(f"Part 2 Example found A: {found_a_ex}")
    if found_a_ex:
        valid = verify_part2(found_a_ex, ex_prog)
        print(f"Part 2 Example Verified: {valid}")
        # Note: Example expected 117440.
    
    # Real Part 2
    lowest_a = find_lowest_a(program)
    print(f"Part 2 Lowest A: {lowest_a}")
    if lowest_a:
        valid = verify_part2(lowest_a, program)
        print(f"Part 2 Valid: {valid}")

if __name__ == '__main__':
    solve()
