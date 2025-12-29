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
        
        # Store the solver object for robust solving of scrambles
        self.solver_cube = None
        
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
        
        # Invalidate the solver_cube since we manually modified the state
        self.solver_cube = None
        
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
            from rubik_solver.Cubie import Cube as SolverCube
            from rubik_solver.Move import Move
            import random
            
            # Use rubik_solver to generate a valid scrambled state
            # We can use the library's shuffle or apply random moves
            c = SolverCube()
            
            # 20 random moves
            moves = ["U", "U'", "D", "D'", "F", "F'", "B", "B'", "R", "R'", "L", "L'"]
            scramble_sequence = [random.choice(moves) for _ in range(20)]
            
            for m_str in scramble_sequence:
                c.move(Move(m_str))
                
            # Get phase string: U, F, R, B, L, D order
            # 'wwwwwwwwwggggggggg...'
            # Note: c.to_naive_cube().to_face_cube() returns FaceCube object
            # Use to_String() to get the string representation
            state_str = c.to_naive_cube().to_face_cube().to_String()
            
            # Map back to GUI state (U, R, F, D, L, B)
            # Solver: U(0-9), F(9-18), R(18-27), B(27-36), L(36-45), D(45-54)
            # GUI:    U(0-9), R(9-18), F(18-27), D(27-36), L(36-45), B(45-54)
            
            # Map chars 'U'->'U', etc.
            # Solver uses Uppercase U, R, F, D, L, B
            char_map = {
                'U': 'U',
                'F': 'F',
                'R': 'R',
                'B': 'B',
                'L': 'L',
                'D': 'D'
            }
            
            # Extract chunks from solver string (Standard Kociemba Order: U, R, F, D, L, B)
            s_u = state_str[0:9]
            s_r = state_str[9:18]
            s_f = state_str[18:27]
            s_d = state_str[27:36]
            s_l = state_str[36:45]
            s_b = state_str[45:54]
            
            # GUI expects list of chars [U, R, F, D, L, B] (Logic order)
            # U face
            gui_u = [char_map[x] for x in s_u]
            # R face
            gui_r = [char_map[x] for x in s_r]
            # F face
            gui_f = [char_map[x] for x in s_f]
            # D face
            gui_d = [char_map[x] for x in s_d]
            # L face
            gui_l = [char_map[x] for x in s_l]
            # B face
            gui_b = [char_map[x] for x in s_b]
            
            # self.cube.state is flat list: U + R + F + D + L + B
            # Note: Logic cube stores in U, R, F, D, L, B order (lines 9-12 of cube_logic: extend f*9 for f in faces)
            # where faces = U, R, F, D, L, B
            # So this matches 1:1.
            self.cube.state = gui_u + gui_r + gui_f + gui_d + gui_l + gui_b
            
            # Store the valid solver object for solving later
            self.solver_cube = c
            
            self.update_all_buttons()
            
        except ImportError:
             # Fallback to logic scramble if lib missing (unlikely now)
            moves = self.cube.scramble()
            self.solver_cube = None
            self.update_all_buttons()
        except Exception as e:
            self.solver_cube = None
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
        # move is a rubik_solver.Move object, str(move) gives "U", "F'", etc.
        self.cube.apply_moves(str(move))
        
        # Apply to solver state (to keep sync)
        if self.solver_cube:
             try:
                 self.solver_cube.move(move)
             except Exception as e:
                 print(f"Sync error: {e}")
                 # If sync fails, invalidate to be safe
                 self.solver_cube = None

        self.update_all_buttons()
        # Schedule next move
        self.root.after(delay, lambda: self.animate_solution(remaining_moves, delay, full_solution_str))

    def solve(self):
        try:
            from rubik_solver.utils import solve as solve_cube
            
            solution = None
            
            # 1. Try using the stored solver_cube (High Fidelity)
            if self.solver_cube is not None:
                try:
                    # Note: solve_cube returns a list of Move objects
                    # We pass a copy if possible? 
                    # Actually rubik_solver.utils.solve copies the cube internally usually
                    # But let's verify. source code of solve:
                    # def solve(cube, ...): c = Astar(cube); return c.solution
                    # It creates a new node. It does not mutate the input cube.
                    solution = solve_cube(self.solver_cube, 'Kociemba')
                except Exception as e:
                    print(f"Object solve failed, falling back: {e}")
                    solution = None
            
            # 2. Fallback to String Construction (Low Fidelity / Manual Edits)
            if solution is None:
                # Use standard U, R, F, D, L, B order and lowercase mapping
                # Helper to get face string
                def get_face(start_idx):
                    return self.cube.state[start_idx : start_idx+9]

                # Extract faces from our state
                face_u = get_face(self.cube.U)
                face_r = get_face(self.cube.R)
                face_f = get_face(self.cube.F)
                face_d = get_face(self.cube.D)
                face_l = get_face(self.cube.L)
                face_b = get_face(self.cube.B)
                
                # Reorder to U, R, F, D, L, B
                ordered_state = face_u + face_r + face_f + face_d + face_l + face_b
                
                # Map to expected colors
                mapping = {
                    'U': 'w',
                    'R': 'r',
                    'F': 'g',
                    'D': 'y',
                    'L': 'o',
                    'B': 'b'
                }
                
                try:
                    state_str = "".join([mapping[c] for c in ordered_state])
                    solution = solve_cube(state_str, 'Kociemba')
                except KeyError:
                    # Handle case where characters are not U,R... (e.g. if logic error)
                    messagebox.showerror("Error", "Invalid characters in cube state.")
                    return
            
            # Start Animation
            if solution is not None:
                # Convert moves to string for display
                moves_str = " ".join([str(m) for m in solution])
                print(f"Solution Steps: {moves_str}")
                
                self.animate_solution(solution, full_solution_str=moves_str)
            else:
                messagebox.showinfo("Info", "No solution found.")
                
        except ImportError:
            messagebox.showerror("Error", "rubik_solver library not installed.\nPlease run: pip install rubik-solver")
        except Exception as e:
            messagebox.showerror("Error", f"Solver error: {str(e)}\n\n(Note: Manual edits must result in a valid cube pattern)")

if __name__ == "__main__":
    root = tk.Tk()
    app = RubiksApp(root)
    root.mainloop()
