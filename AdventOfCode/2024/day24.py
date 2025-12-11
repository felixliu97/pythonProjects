import sys
import re

def parse_input(filename):
    wires = {}
    gates = {}
    
    try:
        with open(filename, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)
        
    parts = content.split('\n\n')
    
    # Parse initial wire values
    for line in parts[0].strip().split('\n'):
        if line.strip():
            name, val = line.strip().split(': ')
            wires[name] = int(val)
            
    # Parse gates
    # Format: x00 AND y00 -> z00
    for line in parts[1].strip().split('\n'):
        if line.strip():
            match = re.match(r'(\w+) (AND|OR|XOR) (\w+) -> (\w+)', line.strip())
            if match:
                i1, op, i2, out = match.groups()
                gates[out] = (op, i1, i2)
                
    return wires, gates

def run_tests():
    print("Running tests...")
    
    # Example 1
    example1_input = """x00: 1
x01: 1
x02: 1
y00: 0
y01: 1
y02: 0

x00 AND y00 -> z00
x01 XOR y01 -> z01
x02 OR y02 -> z02"""
    
    wires_ex1 = {}
    gates_ex1 = {}
    parts1 = example1_input.split('\n\n')
    for line in parts1[0].strip().split('\n'):
        n, v = line.split(': ')
        wires_ex1[n] = int(v)
    for line in parts1[1].strip().split('\n'):
        match = re.match(r'(\w+) (AND|OR|XOR) (\w+) -> (\w+)', line.strip())
        i1, op, i2, out = match.groups()
        gates_ex1[out] = (op, i1, i2)
        
    z_wires_ex1 = sorted([w for w in gates_ex1.keys() if w.startswith('z')])
    res_val_ex1 = 0
    for i, w in enumerate(z_wires_ex1):
        if evaluate(w, wires_ex1, gates_ex1):
            res_val_ex1 |= (1 << i)
            
    print(f"Test Example 1 Result: {res_val_ex1} (Expected 4)")
    expected_p1 = 4
    if res_val_ex1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {res_val_ex1}")
        
    print("✅ Tests completed!")

def evaluate(wire, wires, gates):
    if wire in wires:
        return wires[wire]
    
    if wire not in gates:
        raise ValueError(f"Wire {wire} has no value and no gate definition.")
    
    op, i1, i2 = gates[wire]
    
    val1 = evaluate(i1, wires, gates)
    val2 = evaluate(i2, wires, gates)
    
    if op == 'AND':
        res = val1 & val2
    elif op == 'OR':
        res = val1 | val2
    elif op == 'XOR':
        res = val1 ^ val2
    else:
        raise ValueError(f"Unknown op: {op}")
        
    # Memoize
    wires[wire] = res
    return res

def find_swapped_wires(wires, gates):
    # Heuristic based logic for Part 2 (Ripple Carry Adder validation)
    z_wires = sorted([w for w in gates.keys() if w.startswith('z')])
    last_z = z_wires[-1]
    
    bad_wires = set()
    
    for out_wire, (op, i1, i2) in gates.items():
        # Classify inputs
        has_xy_input = (i1.startswith('x') or i1.startswith('y')) or (i2.startswith('x') or i2.startswith('y'))
        is_xy_op = (i1[0] in 'xy' and i2[0] in 'xy')
        
        # Rule 1: If output is 'z', op MUST be XOR.
        # Exception: The very last z wire is CarryOut, coming from OR usually.
        # Actually z45 is the final carry.
        if out_wire.startswith('z'):
            if op != 'XOR':
                if out_wire != last_z:
                    bad_wires.add(out_wire)
        
        # Rule 2: If op is XOR, and output is NOT 'z', and inputs are NOT x/y.
        # This is expected to be an intermediate Sum (S1 or S2). 
        # Actually, x^y=S1. S1^Cin=Sum. 
        # If it's x^y, input is xy (is_xy_op).
        # If it's S1^Cin, output is z.
        # So if inputs are NOT xy, and output is NOT z, it's WRONG for an XOR.
        if op == 'XOR':
            if not out_wire.startswith('z'):
                if not is_xy_op:
                     bad_wires.add(out_wire)

        # Rule 3: If op is XOR, and inputs ARE x/y, and output IS 'z'.
        # This is x^y -> z. But x^y is Sum1 (intermediate).
        # Sum1 should go to S1^Cin -> Sum.
        # So x^y should NOT go to z directly (unless it's the first bit z00).
        if op == 'XOR' and is_xy_op:
            if out_wire.startswith('z') and out_wire != 'z00':
                bad_wires.add(out_wire)
                
        # Rule 4: "Next Hop" checks.
        # If we have an intermediate XOR (Sum1): x ^ y -> out
        # 'out' MUST be input to an XOR (Sum2) and an AND (Carry2).
        if op == 'XOR' and is_xy_op and out_wire != 'z00':
            consumers = []
            for other_out, (other_op, other_i1, other_i2) in gates.items():
                if out_wire == other_i1 or out_wire == other_i2:
                    consumers.append(other_op)
            
            if 'XOR' not in consumers:
                bad_wires.add(out_wire)
            
        # Refined Next Hop for AND (Carry from half-adder)
        # xn & yn -> C_half.
        # C_half must go to OR.
        # Except x00 & y00 -> C0. C0 goes to XOR/AND of next bit.
        if op == 'AND' and is_xy_op and 'x00' not in (i1, i2):
             consumers = []
             for other_out, (other_op, other_i1, other_i2) in gates.items():
                if out_wire == other_i1 or out_wire == other_i2:
                    consumers.append(other_op)
             
             if 'OR' not in consumers:
                 bad_wires.add(out_wire)

    return ",".join(sorted(list(bad_wires)))

def solve_part1():
    print("--- Part 1 ---")
    wires, gates = parse_input("input-day24.txt")
    
    all_z = sorted([w for w in (set(wires.keys()) | set(gates.keys())) if w.startswith('z')])
    result = 0
    for i, w in enumerate(all_z):
        if evaluate(w, wires, gates):
            result |= (1 << i)
    print(f"Result: {result}")

def solve_part2():
    print("--- Part 2 ---")
    wires, gates = parse_input("input-day24.txt")
    bad_wires_str = find_swapped_wires(wires, gates)
    print(f"Result: {bad_wires_str}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
