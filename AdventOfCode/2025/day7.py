def parse_input(filename):
    with open(filename, 'r') as f:
        lines = f.read().splitlines()
    return lines

def solve(grid):
    if not grid:
        return 0
        
    start_col = -1
    for col, char in enumerate(grid[0]):
        if char == 'S':
            start_col = col
            break
            
    if start_col == -1:
        return 0
        
    active_cols = {start_col}
    split_count = 0
    rows = len(grid)
    cols = len(grid[0])
    
    # Start from the row after S? 
    # The problem says "A tachyon beam enters the manifold at the location marked S; tachyon beams always move downward."
    # S is at row 0. Beams move to row 1, etc.
    # We need to process what happens at each row as the beams arrive.
    # The beam starts at S (row 0). It moves down.
    # So effectively we track beams entering row i.
    
    # Initial state: beam at start_col entering row 0.
    # But row 0 contains S, so it just passes through?
    # "The incoming tachyon beam (|) extends downward from S until it reaches the first splitter"
    # So we can simulate step by step.
    
    # Let's iterate through rows. `active_cols` represents beams at current `r`.
    # We process `grid[r][c]` for each c in active_cols.
    
    for r in range(rows):
        next_active_cols = set()
        
        # If no beams left, we can stop? 
        # "until all of the tachyon beams reach a splitter or exit the manifold"
        # If active_cols is empty, we stop.
        if not active_cols:
            break
            
        for c in active_cols:
            # Check if beam is within bounds (it might have split out of bounds)
            if 0 <= c < cols:
                char = grid[r][c]
                
                if char == '^':
                    split_count += 1
                    # Split left and right
                    next_active_cols.add(c - 1)
                    next_active_cols.add(c + 1)
                else:
                    # Continue straight down
                    next_active_cols.add(c)
            else:
                # Beam out of bounds, it exits the manifold
                pass
                
        active_cols = next_active_cols
        
    return split_count

def solve_part2(grid):
    if not grid:
        return 0
        
    start_col = -1
    for col, char in enumerate(grid[0]):
        if char == 'S':
            start_col = col
            break
            
    if start_col == -1:
        return 0
        
    rows = len(grid)
    cols = len(grid[0])
    memo = {}
    
    def count_timelines(r, c):
        # Base cases
        if r == rows:
            return 1 # Reached bottom
        if c < 0 or c >= cols:
            return 1 # Exited side
            
        state = (r, c)
        if state in memo:
            return memo[state]
            
        char = grid[r][c]
        
        if char == '^':
            # Split
            res = count_timelines(r + 1, c - 1) + count_timelines(r + 1, c + 1)
        else:
            # Continue straight
            res = count_timelines(r + 1, c)
            
        memo[state] = res
        return res

    return count_timelines(0, start_col)

def main():
    grid = parse_input('input-day7.txt')
    
    # Part 1
    result_part1 = solve(grid)
    print(f"Part 1 - Total splits: {result_part1}")
    
    # Part 2
    result_part2 = solve_part2(grid)
    print(f"Part 2 - Total timelines: {result_part2}")

if __name__ == "__main__":
    main()
