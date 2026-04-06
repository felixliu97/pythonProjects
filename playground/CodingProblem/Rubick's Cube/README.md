# Rubik's Cube Solver (Python)

## 1. Problem Analysis

**Core Requirement**: A Python-only program that defaults to generating a random cube state and solving it. It should also support manual validation/input.

**Constraints**:
*   No external C-dependencies (like OpenCV).
*   No complex web stacks.

**Success Criteria**:
*   **Default**: Automatically generates a valid scrambled cube on launch (or via "Scramble" button).
*   **Optional**: User can manually click faces to set a custom state.
*   Outputs a valid solution string in Singmaster notation (e.g., `R U R' U'`) to both the console and a GUI popup.

---

## 2. Architecture Overview

The system follows a simple Input-Process-Output pattern:

1.  **State Input**: A text-based grid or a simple Tkinter window where users click to cycle colors.
2.  **Validation Logic**: Checks that the user has entered exactly 9 of each color and that the centers are unique.
3.  **Solver Core**: Implements a simplified Thistlethwaite or Kociemba wrapper to find the solution.
4.  **Result Formatter**: Translates the algorithm output into readable steps.

---

## 3. Technology Stack

*   **Language**: Python 3.x
*   **Algorithm Library**: `rubik-solver` (pure Python).
*   **UI Framework**: `tkinter` (Python's standard GUI library—requires no pip install).
*   **Logic**: Standard library collections for state management.

---

## 4. Data Model: The "Facelet" Map

To keep things simple, we map the cube to a flat 2D array. A 3x3 cube has 6 faces: Up, Down, Left, Right, Front, Back.
Each face is a $3 \times 3$ grid. In code, we represent this as a single string of 54 characters.
The face order used for the solver is standard Kociemba order: **U, R, F, D, L, B**.

*   Index 0–8: Top Face (U)
*   Index 9–17: Right Face (R)
*   Index 18–27: Front Face (F)
*   ...and so on.

---

## 5. UI Design (Tkinter)

The UI will feature an "unfolded" cube layout (a cross shape).

*   **Interactions**:
    *   **"Scramble" Button** (Default Action): Randomizes the cube state using the `rubik_solver` library logic to ensure a physically solvable state.
    *   **Manual Edit**: Clicking a square cycles through the 6 colors (White, Yellow, Red, Orange, Blue, Green).
*   **Action**: A "Solve" button that gathers the current colors into a string and passes it to the solver.

---

## 6. Implementation Plan (Code Structure)

### Step 1: The Solver Wrapper

We use the `rubik_solver` library for the solving algorithm.

```python
import tkinter as tk
from tkinter import messagebox
from rubik_solver.utils import solve as solver
from rubik_solver.Cubie import Cube as SolverCube

class RubiksApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Cube Solver")
        self.colors = ['white', 'red', 'green', 'yellow', 'orange', 'blue']
        self.facelet_colors = ['white'] * 54  # Initial state: solved
        self.solver_cube = None # Stores valid solver object
        self.buttons = []
        self.create_widgets()
    
    # ... UI creation logic ...
```

### Step 2: Input Handling

*   **Scramble**: Uses `SolverCube` to apply random moves, and stores this object (`self.solver_cube`) for high-fidelity solving.
*   **Manual Edit**: Updates the facelet array. Invalidates `self.solver_cube` because manual edits might create unsolvable states.

### Step 3: Solving Logic

```python
def solve(self):
    try:
        # A. High Fidelity: Use stored object if available
        if self.solver_cube:
             solution = solver(self.solver_cube, 'Kociemba')
             
        # B. Fallback: Construct string from UI colors
        else:
             # Standard Kociemba Order: U, R, F, D, L, B
             # ... mapping logic ...
             state_string = "..." 
             solution = solver(state_string, 'Kociemba')

        moves_str = " ".join(str(m) for m in solution)
        print(f"Solution Steps: {moves_str}")
        self.animate_solution(solution, full_solution_str=moves_str)
        
    except Exception as e:
        messagebox.showerror("Error", f"Solver error: {str(e)}")
```

---

## 7. Security & Performance

*   **Performance**: The pure Python solver might be slightly slower than C-based Kociemba but avoids dependency issues.
*   **Security**: No network calls needed, keeping data entirely private.

---

## 8. Trade-offs

*   **Tkinter vs Pygame**: Tkinter is uglier but requires no installation and is better for "form-style" input.
*   **Manual Input vs CV**: Manual input is tedious (54 clicks), but it's 100% accurate and works in any lighting, unlike OpenCV.

---

## 9. Implementation Milestones

*   **Milestone 1**: Create a 2D "Net" layout in Tkinter where squares change color on click.
*   **Milestone 2**: Write the converter function (GUI colors $\rightarrow$ 54-char string).
*   **Milestone 3**: Integrate `rubik-solver` and display the solution string in a popup.