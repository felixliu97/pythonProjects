import sys

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

def parse_maps(data):
    sections = data.split('\n\n')
    seeds = [int(x) for x in sections[0].split(': ')[1].split()]
    
    maps = []
    for section in sections[1:]:
        lines = section.split('\n')
        # name = lines[0].split(' ')[0]
        ranges = []
        for line in lines[1:]:
            ranges.append(list(map(int, line.split())))
        maps.append(ranges)
    
    return seeds, maps

def get_location(seed, maps):
    current = seed
    for m in maps:
        for dest_start, source_start, length in m:
            if source_start <= current < source_start + length:
                current = dest_start + (current - source_start)
                break
    return current

def process_range(seed_range, map_entries):
    # seed_range: (start, length)
    # map_entries: list of [dest, src, length]
    # returns list of (start, length) in next category
    
    start, length = seed_range
    end = start + length
    
    mapped_ranges = []
    
    # Queue of ranges to process against this map
    # Initially just the one range
    to_process = [(start, length)]
    
    for dest_m, src_m, len_m in map_entries:
        new_to_process = []
        end_m = src_m + len_m
        
        while to_process:
            s, l = to_process.pop()
            e = s + l
            
            # Check overlap between [s, e) and [src_m, end_m)
            o_start = max(s, src_m)
            o_end = min(e, end_m)
            
            if o_start < o_end:
                # We have an overlap [o_start, o_end)
                # Map this part
                mapped_start = dest_m + (o_start - src_m)
                mapped_len = o_end - o_start
                mapped_ranges.append((mapped_start, mapped_len))
                
                # Handle non-overlapping parts
                # Left side [s, o_start)
                if s < o_start:
                    new_to_process.append((s, o_start - s))
                # Right side [o_end, e)
                if e > o_end:
                    new_to_process.append((o_end, e - o_end))
            else:
                # No overlap, keep original
                new_to_process.append((s, l))
        
        to_process = new_to_process
        
    # Anything left in to_process was not mapped by any entry, so it maps 1:1
    mapped_ranges.extend(to_process)
    return mapped_ranges

def solve_ranges(seeds, maps):
    # seeds: list of (start, len)
    current_ranges = seeds
    for m in maps:
        next_ranges = []
        for r in current_ranges:
            next_ranges.extend(process_range(r, m))
        current_ranges = next_ranges
    return current_ranges

def run_tests():
    print("Running tests...")
    
    example_input = """seeds: 79 14 55 13

seed-to-soil map:
50 98 2
52 50 48

soil-to-fertilizer map:
0 15 37
37 52 2
39 0 15

fertilizer-to-water map:
49 53 8
0 11 42
42 0 7
57 7 4

water-to-light map:
88 18 7
18 25 70

light-to-temperature map:
45 77 23
81 45 19
68 64 13

temperature-to-humidity map:
0 69 1
1 0 69

humidity-to-location map:
60 56 37
56 93 4"""
    
    seeds, maps = parse_maps(example_input)
    
    # Part 1 Test
    locations = [get_location(seed, maps) for seed in seeds]
    min_location = min(locations)
    expected_p1 = 35
    
    if min_location == expected_p1:
        print("✅ Part 1 Example passed!")
    else:
        print(f"❌ Part 1 Example failed: Expected {expected_p1}, Got {min_location}")

    # Part 2 Test
    # seeds pairs
    seed_ranges = []
    for i in range(0, len(seeds), 2):
        seed_ranges.append((seeds[i], seeds[i+1]))
        
    final_ranges = solve_ranges(seed_ranges, maps)
    min_location_p2 = min(r[0] for r in final_ranges)
    expected_p2 = 46
    
    if min_location_p2 == expected_p2:
        print("✅ Part 2 Example passed!")
    else:
        print(f"❌ Part 2 Example failed: Expected {expected_p2}, Got {min_location_p2}")
        
    print("✅ Tests completed!")

def solve_part1():
    print("--- Part 1 ---")
    data = parse_input("2023-day5.txt")
    seeds, maps = parse_maps(data)
    min_location = min(get_location(seed, maps) for seed in seeds)
    print(f"Result: {min_location}")

def solve_part2():
    print("--- Part 2 ---")
    data = parse_input("2023-day5.txt")
    seeds, maps = parse_maps(data)
    seed_ranges = []
    for i in range(0, len(seeds), 2):
        seed_ranges.append((seeds[i], seeds[i+1]))
    
    final_ranges = solve_ranges(seed_ranges, maps)
    min_location = min(r[0] for r in final_ranges)
    print(f"Result: {min_location}")

if __name__ == "__main__":
    run_tests()
    solve_part1()
    solve_part2()
