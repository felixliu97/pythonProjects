import tkinter as tk
from tkinter import messagebox
import random
from cube_logic import Cube

# Color definitions
COLORS = {
    'U': 'white',   # Up
    'R': 'red',     # Right
    'F': 'green',   # Front
    'D': 'yellow',  # Down
    'L': 'orange',  # Left
    'B': 'blue'     # Back
}

COLOR_ORDER = ['U', 'R', 'F', 'D', 'L', 'B']

class RubiksApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rubik's Cube Solver")
        
        self.cube = Cube()
        
        # Store scramble moves for reference
        self.scramble_moves = None
        
        self.buttons = []
        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(pady=20, padx=20)

        # Control Panel
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)
        
        tk.Button(control_frame, text="Scramble", command=self.scramble, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Solve", command=self.solve, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Reset", command=self.reset, width=15).pack(side=tk.LEFT, padx=5)

        # Drawing the 6 faces in a cross layout
        # Faces: U, L, F, R, B, D
        # Grid offsets (row, col) for 3x3 blocks
        offsets = {
            'U': (0, 3),
            'L': (3, 0),
            'F': (3, 3),
            'R': (3, 6),
            'B': (3, 9),
            'D': (6, 3)
        }
        
        face_starts = {
            'U': self.cube.U,
            'R': self.cube.R,
            'F': self.cube.F,
            'D': self.cube.D,
            'L': self.cube.L,
            'B': self.cube.B
        }

        self.index_to_button = {}

        for face_name, (row_offset, col_offset) in offsets.items():
            start_idx = face_starts[face_name]
            # Create 3x3 grid for this face
            for r in range(3):
                for c in range(3):
                    idx = start_idx + (r * 3) + c
                    color_code = self.cube.state[idx]
                    color = COLORS[color_code]
                    
                    # Use a closure to capture idx
                    btn = tk.Button(main_frame, bg=color, width=4, height=2,
                                    command=lambda i=idx: self.cycle_color(i))
                    btn.grid(row=row_offset + r, column=col_offset + c, padx=1, pady=1)
                    self.buttons.append(btn)
                    self.index_to_button[idx] = btn
                    
                    # Add Center Label for clarity
                    if r == 1 and c == 1:
                        tk.Label(main_frame, text=face_name, bg=color, font=('Arial', 8, 'bold')).grid(row=row_offset + r, column=col_offset + c)

    def cycle_color(self, idx):
        # Cycle: U -> R -> F -> D -> L -> B -> U
        current_code = self.cube.state[idx]
        current_idx = COLOR_ORDER.index(current_code)
        next_code = COLOR_ORDER[(current_idx + 1) % 6]
        
        self.cube.state[idx] = next_code
        
        # Invalidate scramble since we manually modified the state
        self.scramble_moves = None
        
        self.update_button(idx)

    def update_button(self, idx):
        code = self.cube.state[idx]
        color = COLORS[code]
        btn = self.index_to_button[idx]
        btn.configure(bg=color)

    def update_all_buttons(self):
        for idx in range(54):
            self.update_button(idx)

    def reset(self):
        self.cube.reset()
        self.update_all_buttons()

    def scramble(self):
        try:
            import random
            
            # Reset the cube first
            self.cube.reset()
            
            # Generate and apply random moves
            moves = ["U", "U'", "D", "D'", "F", "F'", "B", "B'", "R", "R'", "L", "L'"]
            scramble_sequence = [random.choice(moves) for _ in range(20)]
            
            self.cube.apply_moves(" ".join(scramble_sequence))
            
            # Store the scramble sequence for solving (we'll reverse it)
            self.scramble_moves = scramble_sequence
            
            self.update_all_buttons()
            
        except Exception as e:
            self.scramble_moves = None
            messagebox.showerror("Error", f"Scramble error: {e}")

    def animate_solution(self, moves_list, delay=500, full_solution_str=None):
        if not moves_list:
            msg = "Cube Solved!"
            if full_solution_str:
                msg += f"\n\nSteps: {full_solution_str}"
            messagebox.showinfo("Solved", msg)
            return

        move = moves_list[0]
        remaining_moves = moves_list[1:]
        
        # Apply to visual/logic cube
        # move is a string like "U", "F'", etc.
        self.cube.apply_moves(move)

        self.update_all_buttons()
        # Schedule next move
        self.root.after(delay, lambda: self.animate_solution(remaining_moves, delay, full_solution_str))

    def solve(self):
        try:
            # Check if we have scramble moves to reverse
            if self.scramble_moves is None:
                messagebox.showinfo("Info", "No scramble to reverse. Use Scramble first, then Solve.\n\n(Manual edits cannot be solved with this method)")
                return
            
            # Create reverse solution by inverting each move and reversing order
            def invert_move(move):
                if move.endswith("'"):
                    return move[0]  # U' -> U
                elif move.endswith("2"):
                    return move  # U2 -> U2 (double move is its own inverse)
                else:
                    return move + "'"  # U -> U'
            
            # Reverse the scramble: apply inverse moves in reverse order
            solution = [invert_move(m) for m in reversed(self.scramble_moves)]
            
            if solution:
                # Convert moves to string for display
                moves_str = " ".join(solution)
                print(f"Solution Steps: {moves_str}")
                
                self.animate_solution(solution, full_solution_str=moves_str)
            else:
                messagebox.showinfo("Info", "Cube is already solved!")
                
        except Exception as e:
            messagebox.showerror("Error", f"Solver error: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RubiksApp(root)
    root.mainloop()
