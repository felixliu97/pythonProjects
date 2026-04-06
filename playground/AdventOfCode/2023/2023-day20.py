import sys
from collections import deque
import math

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def lcm(a, b):
    return abs(a*b) // math.gcd(a, b)

def solve(data):
    lines = data.split('\n')
    modules = {}
    
    # Parse modules
    # name -> {type, destinations, memory}
    # type: %, &, or broadcaster
    
    for line in lines:
        parts = line.split(' -> ')
        name_part = parts[0]
        dests = parts[1].split(', ')
        
        if name_part == 'broadcaster':
            modules['broadcaster'] = {'type': 'broadcaster', 'dests': dests, 'memory': None}
        elif name_part.startswith('%'):
            name = name_part[1:]
            modules[name] = {'type': '%', 'dests': dests, 'memory': 'off'} # off/on
        elif name_part.startswith('&'):
            name = name_part[1:]
            modules[name] = {'type': '&', 'dests': dests, 'memory': {}} # {input: pulse}
            
    # Initialize Conjunction memories
    # Find all inputs for each & module
    for name, mod in modules.items():
        for dest in mod['dests']:
            if dest in modules and modules[dest]['type'] == '&':
                modules[dest]['memory'][name] = 'low'
                
    # Copy for Part 1/Part 2 separation if needed, or restart? 
    # Logic: Module states change.
    
    # Save Initial State for Part 2? A deepcopy is needed if we ruin state in Part 1.
    params_p1 = {'modules': modules, 'part': 1}
    
    # Re-parsing modules is cleaner to ensure fresh state.
    # But let's just make a Deep Copy function or re-parse helper.
    
    def get_fresh_modules():
        mods = {}
        for line in lines:
            parts = line.split(' -> ')
            name_part = parts[0]
            dests = parts[1].split(', ')
            if name_part == 'broadcaster':
                mods['broadcaster'] = {'type': 'broadcaster', 'dests': dests, 'memory': None}
            elif name_part.startswith('%'):
                mods[name_part[1:]] = {'type': '%', 'dests': dests, 'memory': 'off'}
            elif name_part.startswith('&'):
                mods[name_part[1:]] = {'type': '&', 'dests': dests, 'memory': {}}
        for name, mod in mods.items():
            for dest in mod['dests']:
                if dest in mods and mods[dest]['type'] == '&':
                    mods[dest]['memory'][name] = 'low'
        return mods

    modules = get_fresh_modules()
    
    # Part 1
    low_pulses = 0
    high_pulses = 0
    
    for _ in range(1000):
        # Button press -> low to broadcaster
        low_pulses += 1 # Button to broadcaster
        q = deque([('broadcaster', 'low', 'button')])
        
        while q:
            target, pulse, source = q.popleft()
            
            if target not in modules:
                continue
            
            mod = modules[target]
            
            if mod['type'] == 'broadcaster':
                for d in mod['dests']:
                    if pulse == 'low': low_pulses += 1
                    else: high_pulses += 1
                    q.append((d, pulse, target))
                    
            elif mod['type'] == '%':
                if pulse == 'low':
                    if mod['memory'] == 'off':
                        mod['memory'] = 'on'
                        out_pulse = 'high'
                    else:
                        mod['memory'] = 'off'
                        out_pulse = 'low'
                    
                    for d in mod['dests']:
                        if out_pulse == 'low': low_pulses += 1
                        else: high_pulses += 1
                        q.append((d, out_pulse, target))
                        
            elif mod['type'] == '&':
                mod['memory'][source] = pulse
                
                # Check if all inputs high
                all_high = all(p == 'high' for p in mod['memory'].values())
                out_pulse = 'low' if all_high else 'high'
                
                for d in mod['dests']:
                    if out_pulse == 'low': low_pulses += 1
                    else: high_pulses += 1
                    q.append((d, out_pulse, target))
                    
    p1 = low_pulses * high_pulses
    
    # Part 2
    # Find module feeding 'rx'
    modules = get_fresh_modules()
    
    feed_rx = None
    for name, mod in modules.items():
        if 'rx' in mod['dests']:
            feed_rx = name
            break
            
    p2 = 0
    if feed_rx:
        # feed_rx should be a conjunction (&)
        # We need to find when its inputs become high.
        # Its inputs should be conjunctions (or flipflops) that cycle.
        
        # Identify inputs to feed_rx
        rx_sources = []
        for name, mod in modules.items():
            if feed_rx in mod['dests']:
                rx_sources.append(name)
                
        # Only tracks the first time each source sends HIGH to feed_rx
        cycles = {}
        
        presses = 0
        while len(cycles) < len(rx_sources):
            presses += 1
            q = deque([('broadcaster', 'low', 'button')])
            
            while q:
                target, pulse, source = q.popleft()
                
                # Check for monitoring target
                if target == feed_rx and pulse == 'high':
                    if source not in cycles:
                        cycles[source] = presses
                
                if target not in modules:
                    continue
                
                mod = modules[target]
                
                if mod['type'] == 'broadcaster':
                    for d in mod['dests']:
                        q.append((d, pulse, target))
                elif mod['type'] == '%':
                    if pulse == 'low':
                        state = mod['memory']
                        new_state = 'on' if state == 'off' else 'off'
                        mod['memory'] = new_state
                        out_pulse = 'high' if new_state == 'on' else 'low'
                        for d in mod['dests']:
                            q.append((d, out_pulse, target))
                elif mod['type'] == '&':
                    mod['memory'][source] = pulse
                    all_high = all(p == 'high' for p in mod['memory'].values())
                    out_pulse = 'low' if all_high else 'high'
                    for d in mod['dests']:
                        q.append((d, out_pulse, target))
                        
            # Limit to prevent infinite loop if logic fails (e.g. example)
            if presses > 20000 and not cycles: 
                 # Example likely doesn't have rx
                 break
        
        if cycles:
            lcm_val = 1
            for val in cycles.values():
                lcm_val = lcm(lcm_val, val)
            p2 = lcm_val
            
    return p1, p2

def run_tests():
    print("Running tests...")
    example = """broadcaster -> a, b, c
%a -> b
%b -> c
%c -> inv
&inv -> a"""
    
    p1, _ = solve(example) # Part 2 logic detects rx, example has none.
    expected_p1 = 32000000
    
    if p1 == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {p1}")
    
    print("✅ Tests completed!")

def solve_part1_and_2():
    data = parse_input("2023-day20.txt")
    p1, p2 = solve(data)
    print("--- Part 1 ---")
    print(f"Result: {p1}")
    print("--- Part 2 ---")
    print(f"Result: {p2}")

if __name__ == "__main__":
    run_tests()
    solve_part1_and_2()
