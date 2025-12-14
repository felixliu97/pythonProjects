import sys
import copy

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def parse_workflows(block):
    workflows = {}
    for line in block.split('\n'):
        name, rules_str = line[:-1].split('{')
        rules = rules_str.split(',')
        workflows[name] = rules
    return workflows

def parse_parts(block):
    parts = []
    for line in block.split('\n'):
        # {x=787,m=2655,a=1222,s=2876}
        content = line[1:-1]
        part = {}
        for item in content.split(','):
            key, val = item.split('=')
            part[key] = int(val)
        parts.append(part)
    return parts

def process_part(part, workflows):
    current = 'in'
    
    while current not in ('A', 'R'):
        rules = workflows[current]
        matched = False
        for rule in rules:
            if ':' in rule:
                cond, target = rule.split(':')
                # Condition like 'a<2006' OR 'x>10'
                key = cond[0]
                op = cond[1]
                val = int(cond[2:])
                
                part_val = part[key]
                if op == '<':
                    if part_val < val:
                        current = target
                        matched = True
                        break
                elif op == '>':
                    if part_val > val:
                        current = target
                        matched = True
                        break
            else:
                current = rule
                matched = True
                break
                
    return current == 'A'

def count_combinations(ranges, current_wf, workflows):
    if current_wf == 'R':
        return 0
    if current_wf == 'A':
        product = 1
        for key in 'xmas':
            low, high = ranges[key]
            product *= (high - low + 1)
        return product
    
    total = 0
    rules = workflows[current_wf]
    
    current_ranges = copy.deepcopy(ranges)
    
    for rule in rules:
        if ':' in rule:
            cond, target = rule.split(':')
            key = cond[0]
            op = cond[1]
            val = int(cond[2:])
            
            # Split range
            low, high = current_ranges[key]
            
            # True branch range
            true_ranges = copy.deepcopy(current_ranges)
            
            if op == '<':
                # Condition: key < val.
                # Valid range: [low, val-1]
                # New High: min(high, val-1)
                true_high = min(high, val - 1)
                true_low = low
                
                # False branch (continue loop): key >= val
                # Valid range: [val, high]
                false_low = max(low, val)
                false_high = high
                
            elif op == '>':
                # Condition: key > val
                # Valid range: [val+1, high]
                true_low = max(low, val + 1)
                true_high = high
                
                # False branch: key <= val
                # Valid range: [low, val]
                false_high = min(high, val)
                false_low = low
                
            # Process True branch
            if true_low <= true_high:
                true_ranges[key] = (true_low, true_high)
                total += count_combinations(true_ranges, target, workflows)
                
            # Setup False branch for next iteration
            if false_low <= false_high:
                current_ranges[key] = (false_low, false_high)
            else:
                # No possible values left for false branch, stop processing this workflow
                break
        else:
            # Fallback
            total += count_combinations(current_ranges, rule, workflows)
            
    return total

def solve(data):
    w_block, p_block = data.split('\n\n')
    workflows = parse_workflows(w_block)
    parts = parse_parts(p_block)
    
    # Part 1
    total_rating = 0
    for part in parts:
        if process_part(part, workflows):
            total_rating += sum(part.values())
            
    # Part 2
    initial_ranges = {k: (1, 4000) for k in 'xmas'}
    total_combinations = count_combinations(initial_ranges, 'in', workflows)
    
    return total_rating, total_combinations

def run_tests():
    print("Running tests...")
    example = """px{a<2006:qkq,m>2090:A,rfg}
pv{a>1716:R,A}
lnx{m>1548:A,A}
rfg{s<537:gd,x>2440:R,A}
qs{s>3448:A,lnx}
qkq{x<1416:A,crn}
crn{x>2662:A,R}
in{s<1351:px,qqz}
qqz{s>2770:qs,m<1801:hdj,R}
gd{a>3333:R,R}
hdj{m>838:A,pv}

{x=787,m=2655,a=1222,s=2876}
{x=1679,m=44,a=2067,s=496}
{x=2036,m=264,a=79,s=2244}
{x=2461,m=1339,a=466,s=291}
{x=2127,m=1623,a=2188,s=1013}"""
    
    p1, p2 = solve(example)
    expected_p1 = 19114
    expected_p2 = 167409079868000
    
    if p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1}")
        
    if p2 == expected_p2:
         print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {p2}")

    print("✅ Tests completed!")

def solve_part1_and_2():
    data = parse_input("2023-day19.txt")
    p1, p2 = solve(data)
    print("--- Part 1 ---")
    print(f"Result: {p1}")
    print("--- Part 2 ---")
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1_and_2()
