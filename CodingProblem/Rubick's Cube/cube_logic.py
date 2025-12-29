import random

class Cube:
    def __init__(self):
        # Initial solved state
        # Order: U, R, F, D, L, B
        # Colors: U=white, R=red, F=green, D=yellow, L=orange, B=blue
        # We store face names ('U', 'R', 'F', 'D', 'L', 'B') as values
        self.state = []
        faces = ['U', 'R', 'F', 'D', 'L', 'B']
        for f in faces:
            self.state.extend([f] * 9)
            
        # Indices offsets
        self.U, self.R, self.F, self.D, self.L, self.B = 0, 9, 18, 27, 36, 45

    def reset(self):
        faces = ['U', 'R', 'F', 'D', 'L', 'B']
        self.state = []
        for f in faces:
            self.state.extend([f] * 9)

    def get_face(self, face_idx):
        return self.state[face_idx:face_idx+9]

    def set_face(self, face_idx, data):
        self.state[face_idx:face_idx+9] = data

    def rotate_face_clockwise(self, start_idx):
        # Rotate the face stickers (0-8)
        # 0 1 2    6 3 0
        # 3 4 5 -> 7 4 1
        # 6 7 8    8 5 2
        s = self.state[start_idx:start_idx+9]
        new_s = [
            s[6], s[3], s[0],
            s[7], s[4], s[1],
            s[8], s[5], s[2]
        ]
        self.state[start_idx:start_idx+9] = new_s

    def move_U(self):
        self.rotate_face_clockwise(self.U)
        # Adjacent: F(0,1,2) -> L(0,1,2) -> B(0,1,2) -> R(0,1,2) -> F
        # Indices: F:18-20, L:36-38, B:45-47, R:9-11
        F_row = self.state[18:21]
        L_row = self.state[36:39]
        B_row = self.state[45:48]
        R_row = self.state[9:12]
        
        self.state[36:39] = F_row
        self.state[45:48] = L_row
        self.state[9:12]  = B_row
        self.state[18:21] = R_row

    def move_D(self):
        self.rotate_face_clockwise(self.D)
        # Adjacent: F(6,7,8) -> R(6,7,8) -> B(6,7,8) -> L(6,7,8) -> F
        F_row = self.state[24:27]
        R_row = self.state[15:18]
        B_row = self.state[51:54]
        L_row = self.state[42:45]
        
        self.state[15:18] = F_row
        self.state[51:54] = R_row
        self.state[42:45] = B_row
        self.state[24:27] = L_row

    def move_F(self):
        self.rotate_face_clockwise(self.F)
        # Adjacent: U(6,7,8) -> R(0,3,6) -> D(2,1,0) -> L(8,5,2) -> U
        # Wait, standard orientation F CW:
        # U bottom row -> R left col -> D top row (inv?) -> L right col -> U bottom row
        
        # U(6,7,8)
        u_slice = [6, 7, 8]
        # R(0,3,6)
        r_slice = [9, 12, 15]
        # D(2,1,0) (Top row reversed? D is 27-35. Top row 27,28,29)
        # F rotation pushes U bottom to R left.
        # R left goes to D (which part?). R left is adjacent to F right.
        # F right side moves down.
        # So R left (0,3,6) becomes D top (0,1,2) reversed? Or D top (2,1,0).
        # Let's verify D top row is 27,28,29.
        # R left (0,3,6) -> D(2,1,0) i.e. 29, 28, 27.
        d_slice = [29, 28, 27]
        # L right col (8,5,2). L is 36-44. Right col: 38, 41, 44.
        l_slice = [44, 41, 38]
        
        U_vals = [self.state[i] for i in u_slice]
        R_vals = [self.state[i] for i in r_slice]
        D_vals = [self.state[i] for i in d_slice]
        L_vals = [self.state[i] for i in l_slice]
        
        # Apply: U->R, R->D, D->L, L->U
        for k, idx in enumerate(r_slice): self.state[idx] = U_vals[k]
        for k, idx in enumerate(d_slice): self.state[idx] = R_vals[k]
        for k, idx in enumerate(l_slice): self.state[idx] = D_vals[k]
        for k, idx in enumerate(u_slice): self.state[idx] = L_vals[k]

    def move_B(self):
        self.rotate_face_clockwise(self.B)
        # Opposite of F
        # U top row (2,1,0) -> L left col (0,3,6) -> D bottom row (6,7,8) -> R right col (8,5,2) -> U
        
        u_slice = [2, 1, 0]
        l_slice = [36, 39, 42] # L left col (0,3,6)
        d_slice = [33, 34, 35] # D bottom row (6,7,8)
        r_slice = [17, 14, 11] # R right col (8,5,2) i.e. 9+8, 9+5, 9+2
        
        U_vals = [self.state[i] for i in u_slice]
        L_vals = [self.state[i] for i in l_slice]
        D_vals = [self.state[i] for i in d_slice]
        R_vals = [self.state[i] for i in r_slice]
        
        # U->L, L->D, D->R, R->U
        for k, idx in enumerate(l_slice): self.state[idx] = U_vals[k]
        for k, idx in enumerate(d_slice): self.state[idx] = L_vals[k]
        for k, idx in enumerate(r_slice): self.state[idx] = D_vals[k]
        for k, idx in enumerate(u_slice): self.state[idx] = R_vals[k]

    def move_R(self):
        self.rotate_face_clockwise(self.R)
        # U right col (2,5,8) -> B left col (6,3,0) -> D right col (2,5,8) -> F right col (2,5,8) -> U
        
        u_slice = [2, 5, 8]
        b_slice = [51, 48, 45] # B left col (6,3,0) => 45+6, 45+3, 45+0
        d_slice = [29, 32, 35] # D right col (2,5,8) => 27+2...
        f_slice = [20, 23, 26] # F right col (2,5,8)
        
        U_vals = [self.state[i] for i in u_slice]
        B_vals = [self.state[i] for i in b_slice]
        D_vals = [self.state[i] for i in d_slice]
        F_vals = [self.state[i] for i in f_slice]
        
        # U->B, B->D, D->F, F->U
        for k, idx in enumerate(b_slice): self.state[idx] = U_vals[k]
        for k, idx in enumerate(d_slice): self.state[idx] = B_vals[k]
        for k, idx in enumerate(f_slice): self.state[idx] = D_vals[k]
        for k, idx in enumerate(u_slice): self.state[idx] = F_vals[k]

    def move_L(self):
        self.rotate_face_clockwise(self.L)
        # Opposite of R
        # U left col (0,3,6) -> F left col (0,3,6) -> D left col (0,3,6) -> B right col (8,5,2) -> U
        
        u_slice = [0, 3, 6]
        f_slice = [18, 21, 24] # F left
        d_slice = [27, 30, 33] # D left
        b_slice = [53, 50, 47] # B right (8,5,2)
        
        U_vals = [self.state[i] for i in u_slice]
        F_vals = [self.state[i] for i in f_slice]
        D_vals = [self.state[i] for i in d_slice]
        B_vals = [self.state[i] for i in b_slice]
        
        # U->F, F->D, D->B, B->U
        for k, idx in enumerate(f_slice): self.state[idx] = U_vals[k]
        for k, idx in enumerate(d_slice): self.state[idx] = F_vals[k]
        for k, idx in enumerate(b_slice): self.state[idx] = D_vals[k]
        for k, idx in enumerate(u_slice): self.state[idx] = B_vals[k]

    def apply_moves(self, moves_str):
        moves = moves_str.split()
        for move in moves:
            if move == 'U': self.move_U()
            elif move == "U'": self.move_U(); self.move_U(); self.move_U()
            elif move == "U2": self.move_U(); self.move_U()
            
            elif move == 'D': self.move_D()
            elif move == "D'": self.move_D(); self.move_D(); self.move_D()
            elif move == "D2": self.move_D(); self.move_D()
            
            elif move == 'F': self.move_F()
            elif move == "F'": self.move_F(); self.move_F(); self.move_F()
            elif move == "F2": self.move_F(); self.move_F()
            
            elif move == 'B': self.move_B()
            elif move == "B'": self.move_B(); self.move_B(); self.move_B()
            elif move == "B2": self.move_B(); self.move_B()
            
            elif move == 'R': self.move_R()
            elif move == "R'": self.move_R(); self.move_R(); self.move_R()
            elif move == "R2": self.move_R(); self.move_R()
            
            elif move == 'L': self.move_L()
            elif move == "L'": self.move_L(); self.move_L(); self.move_L()
            elif move == "L2": self.move_L(); self.move_L()

    def scramble(self):
        moves = ['U', "U'", 'D', "D'", 'F', "F'", 'B', "B'", 'R', "R'", 'L', "L'"]
        scramble_moves = [random.choice(moves) for _ in range(20)]
        self.apply_moves(" ".join(scramble_moves))
        return " ".join(scramble_moves)
