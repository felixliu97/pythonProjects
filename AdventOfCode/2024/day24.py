import re

def parse_input(filename):
    wires = {}
    gates = {}
    
    try:
        with open(filename, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        return None, None
        
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

def evaluate(wire, wires, gates):
    if wire in wires:
        return wires[wire]
    
    if wire not in gates:
        # Should not happen unless input is incomplete
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

def solve_part2(wires, gates):
    # Retrieve the last Z wire (Carry Out of MSB)
    z_wires = sorted([w for w in gates.keys() if w.startswith('z')])
    last_z = z_wires[-1]
    
    bad_wires = set()
    
    for out_wire, (op, i1, i2) in gates.items():
        # Classify inputs
        has_xy_input = (i1.startswith('x') or i1.startswith('y')) or (i2.startswith('x') or i2.startswith('y'))
        # Standard input gates usually take xNN and yNN.
        # Check specific edge case for x00, y00?
        is_xy_op = (i1[0] in 'xy' and i2[0] in 'xy')
        
        # Rule 1: If output is 'z', op MUST be XOR.
        # Exception: The very last z wire is the final carry, so it's usually OR (or whatever produces CarryOut).
        # Actually, in a ripple carry adder, z_i is Sum_i = A xor B xor C.
        # The last z is the CarryOut of standard adders. 
        # For standard full adder chain: Gates outputting to zNN must be XOR.
        # But wait, z45 (last one) is the final carry. The final carry comes from an OR gate (Carry1 | Carry2).
        if out_wire.startswith('z'):
            if op != 'XOR':
                if out_wire != last_z:
                    bad_wires.add(out_wire)
        
        # Rule 2: If op is XOR, and output is NOT 'z', and inputs are NOT x/y.
        # This is the "2nd XOR" (Sum2 = Sum1 ^ Cin).
        # If it's an XOR gate, it computes a Sum bit.
        # If input is x/y, it computes Sum1 (intermediate).
        # If input is NOT x/y, it computes Final Sum (z).
        # So if inputs are NOT x/y, output MUST be 'z'.
        if op == 'XOR':
            if not out_wire.startswith('z'):
                if not is_xy_op:
                     bad_wires.add(out_wire)

        # Rule 3: If op is XOR, and inputs ARE x/y, and output IS 'z'.
        # This is the "1st XOR" (Sum1 = x ^ y).
        # It should go to the 2nd XOR, not directly to z.
        # Exception: z00. Sum0 = x00 ^ y00. There is no carry in.
        if op == 'XOR' and is_xy_op:
            if out_wire.startswith('z') and out_wire != 'z00':
                bad_wires.add(out_wire)
                
        # Rule 4: "Next Hop" checks.
        # If we have an intermediate XOR (Sum1): x ^ y -> out
        # 'out' MUST be input to an XOR (Sum2) and an AND (Carry2).
        # Except for x00^y00 (Sum0) which only goes to AND (Carry0)? Actually z00 is output.
        # x00^y00 -> z00.
        # x00&y00 -> carry0.
        # For n > 0:
        # xn^yn -> S1. S1 splits to (S1 ^ Cin -> Zn) and (S1 & Cin -> C2).
        # So S1 must be input to XOR and AND.
        
        if op == 'XOR' and is_xy_op and out_wire != 'z00':
            # Check consumers of out_wire
            consumers = []
            for other_out, (other_op, other_i1, other_i2) in gates.items():
                if out_wire == other_i1 or out_wire == other_i2:
                    consumers.append(other_op)
            
            # Must have XOR and AND
            # If not, 'out_wire' is likely swapped.
            # However, if 'out_wire' was already flagged, we don't strictly need to re-flag.
            # But if it wasn't flagged (e.g. wrong op), this might catch it?
            # Actually, if S1 is swapped with something else, S1 won't go to XOR/AND.
            if 'XOR' not in consumers:
                bad_wires.add(out_wire) # Logic might be flawed
                # Let's refine. If S1 feeds an OR, that's wrong.
                pass
            
            # Note: This logic is tricky because if S1 points to wrong gates, S1 might be correct but consumers are wrong?
            # No, if S1 is correct, it MUST act as input to XOR and AND.
            # If it's input to OR, then 'out_wire' itself might be wrong?
            # Or the wires it connects to are wrong?
            # Let's just rely on rules 1-3 first.
            
        # Refined Next Hop for AND (Carry1)
        # xn & yn -> C1.
        # C1 must go to OR.
        # Except x00 & y00 -> C0. C0 goes to XOR (Sum1) and AND (Carry2 of next bit).
        if op == 'AND' and is_xy_op and 'x00' not in (i1, i2):
             consumers = []
             for other_out, (other_op, other_i1, other_i2) in gates.items():
                if out_wire == other_i1 or out_wire == other_i2:
                    consumers.append(other_op)
             
             if 'OR' not in consumers:
                 bad_wires.add(out_wire)

    return ",".join(sorted(list(bad_wires)))

def solve():
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
            
    print(f"Example 1 Result: {res_val_ex1} (Expected 4)")
    assert res_val_ex1 == 4
    print("Example 1 passed!")

    # Real Input
    wires, gates = parse_input('input-day24.txt')
    if wires is not None:
        all_z = sorted([w for w in (set(wires.keys()) | set(gates.keys())) if w.startswith('z')])
        
        # Part 1
        result = 0
        for i, w in enumerate(all_z):
            if evaluate(w, wires, gates):
                result |= (1 << i)
        print(f"\nPart 1 Final Result: {result}")
        
        # Part 2
        bad_wires_str = solve_part2(wires, gates)
        print(f"Part 2 Swapped Wires: {bad_wires_str}")
        
    else:
        print("input-day24.txt not found.")

if __name__ == '__main__':
    solve()
