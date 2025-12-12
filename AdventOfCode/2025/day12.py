import sys
import time

sys.setrecursionlimit(10000)

def parse_input(filename):
    try:
        with open(filename, 'r') as f:
            content = f.read().strip()
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        sys.exit(1)

    sections = content.split('\n\n')
    
    shapes_raw = []
    queries = []
    
    # Process sections to separate shapes and queries
    # Shapes usually come first, numbered 0:, 1:, etc.
    # Queries look like WxH: ...
    
    for section in sections:
        lines = section.strip().split('\n')
        if not lines:
            continue
            
        header = lines[0].strip()
        
        if header.endswith(':'): # It's a shape
            # Check if it looks like "0:"
            parts = header.split(':')
            if len(parts[0]) <= 2 and parts[0].isdigit():
                idx = int(parts[0])
                grid = [list(line) for line in lines[1:]]
                shapes_raw.append((idx, grid))
        elif 'x' in header and ':' in header: # It's a query or block of queries
            # 46x45: 71 55 ...
            for line in lines:
                if 'x' in line and ':' in line:
                    dim_part, counts_part = line.split(':')
                    w_str, h_str = dim_part.split('x')
                    w, h = int(w_str), int(h_str)
                    counts = list(map(int, counts_part.strip().split()))
                    # DEBUG:
                    # if w == 46 and h == 45:
                    #     print(f"DEBUG PARSE: Found 46x45, counts: {counts}")
                    queries.append({
                        'w': w, 'h': h,
                        'counts': counts,
                        'line': line # for debug/display
                    })

    # Sort shapes by index just in case
    shapes_raw.sort(key=lambda x: x[0])
    shapes = [grid for _, grid in shapes_raw]
    
    return shapes, queries

class Shape:
    def __init__(self, grid):
        self.variants = self._generate_variants(grid)

    def _generate_variants(self, grid):
        variants = set()
        
        # Base grid
        current = grid
        
        for _ in range(2): # Flip
            for _ in range(4): # Rotate
                # Normalize and add (as tuple of tuples for hashing)
                normalized = self._normalize(current)
                variants.add(normalized)
                current = self._rotate(current)
            current = self._flip(current)
            
        return list(variants)

    def _rotate(self, grid):
        # Rotate 90 deg clockwise
        return list(zip(*grid[::-1]))

    def _flip(self, grid):
        # Flip vertically
        return grid[::-1]

    def _normalize(self, grid):
        # 1. Trim empty rows/cols
        if not grid: return ()
        
        rows = len(grid)
        cols = len(grid[0])
        
        min_r, max_r = rows, -1
        min_c, max_c = cols, -1
        
        has_hash = False
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == '#':
                    has_hash = True
                    min_r = min(min_r, r)
                    max_r = max(max_r, r)
                    min_c = min(min_c, c)
                    max_c = max(max_c, c)
        
        if not has_hash:
            return ()
            
        cropped = []
        for r in range(min_r, max_r + 1):
            row = []
            for c in range(min_c, max_c + 1):
                row.append(grid[r][c])
            cropped.append(tuple(row))
            
        return tuple(cropped)

    def get_bitmasks(self, grid_width):
        """
        Convert variants into bitmasks (integer offsets) for a specific grid width.
        Returns a list of (width, height, integer_mask) tuples.
        """
        masks = []
        for v in self.variants:
            h = len(v)
            if h == 0: continue
            w = len(v[0])
            
            # If variant is wider than grid, skip
            if w > grid_width:
                continue
                
            mask = 0
            for r in range(h):
                for c in range(w):
                    if v[r][c] == '#':
                        # Convert (r, c) to linear index
                        # Cell (0,0) is High Bit? No, let's say index 0 is LSB or similar.
                        # Standard convention: Index = r * grid_width + c.
                        # We'll use 0 as the "current cell" in the search, so relative to top-left of shape.
                        idx = r * grid_width + c
                        mask |= (1 << idx)
            masks.append({'w': w, 'h': h, 'mask': mask, 'grid': v})
        return masks

def run_tests():
    print("Running tests...")
    
    # Test Parsing
    shapes, queries = parse_input("input-day12.txt")
    print(f"Parsed {len(shapes)} shapes and {len(queries)} queries.")
    
    assert len(shapes) == 6, "Should create 6 shapes"
    
    # Test Shape Normalization
    s0 = Shape(shapes[0])
    print(f"Shape 0 has {len(s0.variants)} unique variants.")
    
    # Visual check of variants
    for v in s0.variants:
        for r in v:
            print("".join(r))
        print("---")

    print("✅ Tests completed!")

class BitmaskSolver:
    def __init__(self, shapes):
        self.shapes = shapes
        # Cache for shape variants per width: {width: {shape_idx: [masks]}}
        self.cache = {}

    def get_shape_masks(self, width, shape_idx):
        if width not in self.cache:
            self.cache[width] = {}
        if shape_idx not in self.cache[width]:
            self.cache[width][shape_idx] = self.shapes[shape_idx].get_bitmasks(width)
        return self.cache[width][shape_idx]

    def solve_query(self, query):
        w, h = query['w'], query['h']
        counts = list(query['counts'])
        
        # 1. Area Check
        grid_area = w * h
        presents_area = 0
        shape_areas = []
        for idx, count in enumerate(counts):
            grid0 = self.shapes[idx].variants[0]
            area = sum(row.count('#') for row in grid0)
            presents_area += count * area
            shape_areas.append((area, idx))
            
        slack = grid_area - presents_area
        # print(f"Query {w}x{h}, Area {presents_area}, Slack {slack}")
        
        if slack < 0:
            return False
            
        # 2. Setup Backtracking
        # Precompute candidate order (Largest Area First)
        # Only include present types likely to be used? No, order all types.
        # We will iterate this static list and check counts[p_idx] > 0 dynamically.
        shape_areas.sort(key=lambda x: x[0], reverse=True)
        priority_indices = [idx for _, idx in shape_areas]
        
        # Cache masks for this query
        query_masks = []
        for i in range(len(counts)):
            query_masks.append(self.get_shape_masks(w, i))
        
        return self._backtrack(0, counts, slack, w, h, query_masks, priority_indices)

    def _backtrack(self, state, counts, slack, w, h, query_masks, priority_indices):
        # Find first empty cell (Lowest Zero Bit)
        # (~state) has 1s at empty positions. 
        # But integers are infinite. We need to mask it.
        # However, purely trailing zeros of (~state) works if we treat it right.
        # (~state & -~state).bit_length() - 1 gives index of lowest set bit.
        # Note: ~state is -state - 1. 
        # Python handling of negative numbers might make this tricky with infinite 1s.
        # Safest: Use a mask.
        # Note: (state + 1) & ~state isolates the lowest zero bit IF state starts at 0 and grows?
        # Example: state=1011 (binary). ~state=...1110100.
        # state+1=1100. (state+1) & ~state = 0100. Correct (index 2).
        # Example: state=0. ~state=...1111. state+1=1. Result=1 (index 0). Correct.
        # Example: state=11. ~state=...1100. state+1=100. Result=100. Correct.
        low_zero = (state + 1) & ~state
        first_empty = low_zero.bit_length() - 1
        
        if first_empty >= w * h:
            # Full grid or out of bounds (effectively full)
            if sum(counts) == 0:
                return True
            return False

        # Try to place a present (Optimized Order)
        for p_idx in priority_indices:
            if counts[p_idx] > 0:
                # Try all variants of this present
                masks = query_masks[p_idx]
                
                for m in masks:
                    # Coordinate extraction
                    if (first_empty % w) + m['w'] > w: continue
                    # row check unnecessary if mask is valid and we are at first_empty? 
                    # Yes, precomputed masks are valid for width W.
                    # But wait, mask bits: idx = r*w + c.
                    # If we shift by first_empty, we push bits to higher indices.
                    # We MUST check if shifting pushes bits beyond grid height? 
                    # No, strictly speaking if (state & shifted) == 0, we can't overlap existing blocks.
                    # But we could wrap around? 
                    # No, `get_bitmasks` generated linear masks assuming (0,0) placement.
                    # Shifting by linear index `first_empty` preserves relative structure.
                    # BUT: if mask has width 2, and we are at last column, `first_empty % w` check handles wrap.
                    # Height check: `(first_empty // w) + m['h'] > h` implies bits go off bottom.
                    # But simpler check: `shifted_mask >= (1 << (w*h))` implies out of bounds.
                    
                    shifted_mask = m['mask'] << first_empty
                    
                    if shifted_mask.bit_length() > w * h: continue
                    
                    # Overlap check
                    if (state & shifted_mask) == 0:
                        # Place it
                        counts[p_idx] -= 1
                        if self._backtrack(state | shifted_mask, counts, slack, w, h, query_masks, priority_indices):
                            return True
                        # Backtrack
                        counts[p_idx] += 1

        # Try to skip (Slack) - ONLY if placement failed
        if slack > 0:
            # Place "slack" at first_empty
            if self._backtrack(state | (1 << first_empty), counts, slack - 1, w, h, query_masks, priority_indices):
                return True

        return False

def solve_part1():
    print("--- Part 1 ---")
    shapes_raw, queries = parse_input("input-day12.txt")
    
    # Preprocess shapes
    shapes = [Shape(grid) for grid in shapes_raw]
    solver = BitmaskSolver(shapes)
    
    total_valid = 0
    t0 = time.time()
    
    for i, q in enumerate(queries):
        if solver.solve_query(q):
            total_valid += 1
        if (i + 1) % 100 == 0:
             print(f"Processed {i+1}/{len(queries)} queries... (Current valid: {total_valid})")

    duration = time.time() - t0
    print(f"Result: {total_valid}")
    print(f"Time: {duration:.2f}s")

if __name__ == "__main__":
    run_tests()
    solve_part1()
