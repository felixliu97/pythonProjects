"""
Monopoly GUI - Enhanced Realistic Board Layout

A Tkinter-based graphical interface styled like the real Monopoly board game
with classic square layout, colored property bands, animated dice, and
polished player panels.
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
from typing import Optional
import random
import math

from .game import MonopolyGame
from .player import Player
from .board import Board, SpecialSpace, SpaceType
from .property import Property, Street, Railroad, Utility, PropertyColor
from .dice import DiceRoll


# Classic Monopoly color scheme
COLORS = {
    "board_bg": "#C8E6C9",      # Light green board
    "board_center": "#C8E6C9", 
    "go_green": "#00A651",
    "jail_orange": "#F7941D",
    "parking_red": "#ED1C24",
    "gotojail_blue": "#0072BC",
    "panel_bg": "#2C3E50",
    "panel_fg": "#ECF0F1",
    "active_border": "#FFD700",
    "button_blue": "#3498DB",
    "button_green": "#27AE60",
    "button_red": "#E74C3C",
    "button_purple": "#9B59B6",
    "money_green": "#27AE60",
}

PROPERTY_COLORS = {
    PropertyColor.BROWN: "#8B4513",
    PropertyColor.LIGHT_BLUE: "#87CEEB",
    PropertyColor.PINK: "#D93A96",
    PropertyColor.ORANGE: "#F7941D",
    PropertyColor.RED: "#ED1C24",
    PropertyColor.YELLOW: "#FFED00",
    PropertyColor.GREEN: "#1FB25A",
    PropertyColor.DARK_BLUE: "#0072BB",
}

DEFAULT_PLAYERS = [
    ("Alice", "🎩", "#E74C3C"),
    ("Bob", "🚗", "#3498DB"),
    ("Charlie", "🐕", "#27AE60"),
    ("Diana", "⛵", "#9B59B6"),
]


class MonopolyGUI:
    """
    Enhanced Monopoly GUI with realistic board layout.
    """
    
    def __init__(self, num_players: int = 4):
        self.root = tk.Tk()
        self.root.title("🎲 MONOPOLY")
        self.root.geometry("1400x900")
        self.root.configure(bg=COLORS["panel_bg"])
        self.root.resizable(True, True)
        
        # Initialize game
        self.game = MonopolyGame()
        self._setup_players(num_players)
        
        # GUI state
        self.waiting_for_buy_decision = False
        self.current_property: Optional[Property] = None
        self.cell_positions = []
        
        # Build UI
        self._create_widgets()
        self._update_display()
    
    def _setup_players(self, num_players: int) -> None:
        """Add default players."""
        for i in range(min(num_players, 4)):
            name, token, _ = DEFAULT_PLAYERS[i]
            self.game.add_player(name, token)
    
    def _create_widgets(self) -> None:
        """Create all GUI widgets."""
        # Main container with grid
        self.root.grid_columnconfigure(0, weight=3)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Left: Board
        self._create_board_area()
        
        # Right: Control panel
        self._create_control_panel()
    
    def _create_board_area(self) -> None:
        """Create the realistic game board."""
        board_frame = tk.Frame(self.root, bg=COLORS["panel_bg"], padx=20, pady=20)
        board_frame.grid(row=0, column=0, sticky="nsew")
        board_frame.grid_rowconfigure(0, weight=1)
        board_frame.grid_columnconfigure(0, weight=1)
        
        # Canvas for board
        self.board_size = 700
        self.board_canvas = tk.Canvas(
            board_frame,
            width=self.board_size,
            height=self.board_size,
            bg=COLORS["board_bg"],
            highlightthickness=3,
            highlightbackground="#333"
        )
        self.board_canvas.grid(row=0, column=0)
        
        self._draw_board()
    
    def _draw_board(self) -> None:
        """Draw the classic Monopoly board layout."""
        canvas = self.board_canvas
        canvas.delete("all")
        
        size = self.board_size
        corner_size = 80
        cell_width = (size - 2 * corner_size) // 9
        cell_height = 55
        
        self.cell_positions = []
        
        # Draw board border
        canvas.create_rectangle(2, 2, size-2, size-2, outline="#333", width=3)
        
        # === BOTTOM ROW (GO to Jail - positions 0-10) ===
        # GO (position 0) - bottom right corner
        self._draw_corner(canvas, size - corner_size, size - corner_size, 
                         corner_size, "GO", COLORS["go_green"], 0)
        
        # Bottom row properties (positions 1-9)
        for i in range(9):
            x = size - corner_size - (i + 1) * cell_width
            y = size - cell_height
            space = self.game.board.get_space(i + 1)
            self._draw_cell(canvas, x, y, cell_width, cell_height, space, i + 1, "bottom")
        
        # Jail (position 10) - bottom left corner
        self._draw_corner(canvas, 0, size - corner_size, corner_size, 
                         "JAIL", COLORS["jail_orange"], 10)
        
        # === LEFT COLUMN (positions 11-19) ===
        for i in range(9):
            x = 0
            y = size - corner_size - (i + 1) * cell_width
            space = self.game.board.get_space(11 + i)
            self._draw_cell(canvas, x, y, cell_height, cell_width, space, 11 + i, "left")
        
        # Free Parking (position 20) - top left corner
        self._draw_corner(canvas, 0, 0, corner_size, "FREE\nPARKING", 
                         COLORS["parking_red"], 20)
        
        # === TOP ROW (positions 21-29) ===
        for i in range(9):
            x = corner_size + i * cell_width
            y = 0
            space = self.game.board.get_space(21 + i)
            self._draw_cell(canvas, x, y, cell_width, cell_height, space, 21 + i, "top")
        
        # Go to Jail (position 30) - top right corner
        self._draw_corner(canvas, size - corner_size, 0, corner_size, 
                         "GO TO\nJAIL", COLORS["gotojail_blue"], 30)
        
        # === RIGHT COLUMN (positions 31-39) ===
        for i in range(9):
            x = size - cell_height
            y = corner_size + i * cell_width
            space = self.game.board.get_space(31 + i)
            self._draw_cell(canvas, x, y, cell_height, cell_width, space, 31 + i, "right")
        
        # === CENTER AREA ===
        self._draw_center(canvas, corner_size, cell_height, size)
        
        # Draw player tokens
        self._draw_tokens()
    
    def _draw_corner(self, canvas, x, y, size, text, color, pos):
        """Draw a corner square."""
        canvas.create_rectangle(x, y, x + size, y + size, 
                               fill=color, outline="#333", width=2)
        canvas.create_text(x + size/2, y + size/2, text=text,
                          font=("Helvetica", 10, "bold"), fill="white",
                          justify=tk.CENTER)
        self.cell_positions.append((x, y, size, size, pos))
    
    def _draw_cell(self, canvas, x, y, w, h, space, pos, side):
        """Draw a property/space cell with color band and ownership indicator."""
        # Determine ownership border color
        owner_color = None
        if isinstance(space, Property) and space.owner:
            player_idx = self.game.players.index(space.owner)
            if player_idx < len(DEFAULT_PLAYERS):
                owner_color = DEFAULT_PLAYERS[player_idx][2]
        
        # Main cell with ownership border if owned
        if owner_color:
            # Draw ownership border (thicker, colored)
            canvas.create_rectangle(x-2, y-2, x + w + 2, y + h + 2,
                                   fill=owner_color, outline=owner_color, width=0)
        canvas.create_rectangle(x, y, x + w, y + h, 
                               fill="white", outline="#333", width=1)
        
        # Color band for streets
        band_size = 12
        if isinstance(space, Street):
            color = PROPERTY_COLORS.get(space.color, "#888")
            if side == "bottom":
                canvas.create_rectangle(x, y, x + w, y + band_size, fill=color)
            elif side == "top":
                canvas.create_rectangle(x, y + h - band_size, x + w, y + h, fill=color)
            elif side == "left":
                canvas.create_rectangle(x + w - band_size, y, x + w, y + h, fill=color)
            elif side == "right":
                canvas.create_rectangle(x, y, x + band_size, y + h, fill=color)
        
        # Special icons
        icon = ""
        if isinstance(space, Railroad):
            icon = "🚂"
        elif isinstance(space, Utility):
            icon = "💡" if "Electric" in space.name else "💧"
        elif isinstance(space, SpecialSpace):
            if space.space_type == SpaceType.CHANCE:
                icon = "❓"
            elif space.space_type == SpaceType.COMMUNITY_CHEST:
                icon = "📦"
            elif space.space_type == SpaceType.INCOME_TAX:
                icon = "💰"
            elif space.space_type == SpaceType.LUXURY_TAX:
                icon = "💎"
        
        # Draw name (abbreviated)
        name = space.name[:7] if len(space.name) > 7 else space.name
        if icon:
            canvas.create_text(x + w/2, y + h/2 - 5, text=icon, font=("Helvetica", 12))
            canvas.create_text(x + w/2, y + h/2 + 10, text=name, 
                              font=("Helvetica", 6), width=w-4)
        else:
            canvas.create_text(x + w/2, y + h/2, text=name, 
                              font=("Helvetica", 7), width=w-4)
        
        # Draw houses/hotels
        if isinstance(space, Street) and space.houses > 0:
            self._draw_houses(canvas, x, y, w, h, space.houses, side)
        
        self.cell_positions.append((x, y, w, h, pos))
    
    def _draw_houses(self, canvas, x, y, w, h, houses, side):
        """Draw house/hotel indicators."""
        if houses == 5:  # Hotel
            color = "red"
            count = 1
        else:
            color = "green"
            count = houses
        
        size = 6
        for i in range(count):
            if side == "bottom":
                hx = x + 5 + i * (size + 2)
                hy = y + 15
            elif side == "top":
                hx = x + 5 + i * (size + 2)
                hy = y + h - 20
            elif side == "left":
                hx = x + w - 18
                hy = y + 5 + i * (size + 2)
            else:
                hx = x + 12
                hy = y + 5 + i * (size + 2)
            
            canvas.create_rectangle(hx, hy, hx + size, hy + size, 
                                   fill=color, outline="black")
    
    def _draw_center(self, canvas, corner_size, cell_height, size):
        """Draw center area with logo and dice."""
        cx = size // 2
        cy = size // 2
        
        # Monopoly logo
        canvas.create_text(cx, cy - 80, text="MONOPOLY",
                          font=("Impact", 36, "bold"), fill="#B22222")
        
        # Dice area
        self.dice_frame_x = cx - 50
        self.dice_frame_y = cy - 20
        canvas.create_rectangle(cx - 70, cy - 40, cx + 70, cy + 40,
                               fill="#E8E8E8", outline="#333", width=2)
        
        # Dice placeholders
        self._draw_dice(canvas, cx - 35, cy, 0)
        self._draw_dice(canvas, cx + 35, cy, 0)
        
        # Status text
        self.status_text_id = canvas.create_text(cx, cy + 100, text="",
                                                 font=("Helvetica", 14), fill="#333")
    
    def _draw_dice(self, canvas, x, y, value):
        """Draw a single die."""
        size = 40
        canvas.create_rectangle(x - size/2, y - size/2, x + size/2, y + size/2,
                               fill="white", outline="#333", width=2)
        
        if value == 0:
            canvas.create_text(x, y, text="?", font=("Helvetica", 20, "bold"), fill="#CCC")
            return
        
        dot_positions = {
            1: [(0, 0)],
            2: [(-10, -10), (10, 10)],
            3: [(-10, -10), (0, 0), (10, 10)],
            4: [(-10, -10), (10, -10), (-10, 10), (10, 10)],
            5: [(-10, -10), (10, -10), (0, 0), (-10, 10), (10, 10)],
            6: [(-10, -10), (10, -10), (-10, 0), (10, 0), (-10, 10), (10, 10)],
        }
        
        for dx, dy in dot_positions.get(value, []):
            canvas.create_oval(x + dx - 4, y + dy - 4, x + dx + 4, y + dy + 4,
                              fill="black")
    
    def _draw_tokens(self) -> None:
        """Draw player tokens on the board with colored backgrounds."""
        canvas = self.board_canvas
        
        # Group by position
        pos_players = {}
        for player in self.game.players:
            if not player.is_bankrupt:
                p = player.position
                if p not in pos_players:
                    pos_players[p] = []
                pos_players[p].append(player)
        
        # Draw tokens
        for pos, players in pos_players.items():
            # Find cell position
            for x, y, w, h, cell_pos in self.cell_positions:
                if cell_pos == pos:
                    for i, player in enumerate(players):
                        ox = 12 + (i % 2) * 22
                        oy = 28 + (i // 2) * 20
                        
                        # Get player color
                        player_idx = self.game.players.index(player)
                        if player_idx < len(DEFAULT_PLAYERS):
                            player_color = DEFAULT_PLAYERS[player_idx][2]
                        else:
                            player_color = "#888"
                        
                        # Draw colored circle background
                        radius = 12
                        cx, cy = x + ox, y + oy
                        canvas.create_oval(
                            cx - radius, cy - radius, 
                            cx + radius, cy + radius,
                            fill=player_color, outline="white", width=2
                        )
                        
                        # Draw token emoji on top
                        canvas.create_text(cx, cy, text=player.token,
                                          font=("Helvetica", 12))
                    break
    
    def _create_control_panel(self) -> None:
        """Create right-side control panel."""
        panel = tk.Frame(self.root, bg=COLORS["panel_bg"], padx=15, pady=15)
        panel.grid(row=0, column=1, sticky="nsew")
        
        # Current player section
        self._create_current_player_section(panel)
        
        # Dice display
        self._create_dice_section(panel)
        
        # Action buttons
        self._create_buttons_section(panel)
        
        # All players list
        self._create_players_section(panel)
        
        # Game log
        self._create_log_section(panel)
    
    def _create_current_player_section(self, parent):
        """Current player info."""
        frame = tk.LabelFrame(parent, text="🎯 Current Turn", 
                             font=("Helvetica", 12, "bold"),
                             bg=COLORS["panel_bg"], fg="white")
        frame.pack(fill=tk.X, pady=(0, 10))
        
        self.current_player_label = tk.Label(frame, text="", 
                                            font=("Helvetica", 18, "bold"),
                                            bg=COLORS["panel_bg"], fg="#3498DB")
        self.current_player_label.pack(pady=5)
        
        self.money_label = tk.Label(frame, text="",
                                   font=("Helvetica", 16),
                                   bg=COLORS["panel_bg"], fg=COLORS["money_green"])
        self.money_label.pack(pady=5)
        
        self.position_label = tk.Label(frame, text="",
                                       font=("Helvetica", 11),
                                       bg=COLORS["panel_bg"], fg="white")
        self.position_label.pack(pady=5)
    
    def _create_dice_section(self, parent):
        """Dice display section."""
        frame = tk.LabelFrame(parent, text="🎲 Dice", 
                             font=("Helvetica", 12, "bold"),
                             bg=COLORS["panel_bg"], fg="white")
        frame.pack(fill=tk.X, pady=(0, 10))
        
        self.dice_label = tk.Label(frame, text="⚀ ⚀",
                                  font=("Helvetica", 32),
                                  bg=COLORS["panel_bg"], fg="white")
        self.dice_label.pack(pady=5)
        
        self.dice_result_label = tk.Label(frame, text="Roll to start!",
                                         font=("Helvetica", 12),
                                         bg=COLORS["panel_bg"], fg="#AAA")
        self.dice_result_label.pack(pady=5)
    
    def _create_buttons_section(self, parent):
        """Action buttons."""
        frame = tk.LabelFrame(parent, text="⚡ Actions",
                             font=("Helvetica", 12, "bold"),
                             bg=COLORS["panel_bg"], fg="white")
        frame.pack(fill=tk.X, pady=(0, 10))
        
        btn_style = {"font": ("Helvetica", 11, "bold"), "width": 18, "height": 2,
                    "relief": tk.FLAT, "cursor": "hand2"}
        
        self.roll_btn = tk.Button(frame, text="🎲 Roll Dice",
                                 command=self._on_roll,
                                 bg=COLORS["button_blue"], fg="white", **btn_style)
        self.roll_btn.pack(pady=3, padx=10)
        
        self.buy_btn = tk.Button(frame, text="🏠 Buy Property",
                                command=self._on_buy, state=tk.DISABLED,
                                bg=COLORS["button_green"], fg="white", **btn_style)
        self.buy_btn.pack(pady=3, padx=10)
        
        self.build_btn = tk.Button(frame, text="🏗️ Build House",
                                  command=self._on_build,
                                  bg=COLORS["button_purple"], fg="white", **btn_style)
        self.build_btn.pack(pady=3, padx=10)
        
        self.end_btn = tk.Button(frame, text="⏭️ End Turn",
                                command=self._on_end_turn,
                                bg=COLORS["button_red"], fg="white", **btn_style)
        self.end_btn.pack(pady=3, padx=10)
    
    def _create_players_section(self, parent):
        """All players list with owned properties."""
        # Create scrollable frame for players
        self.players_frame = tk.LabelFrame(parent, text="👥 Players & Properties",
                             font=("Helvetica", 12, "bold"),
                             bg=COLORS["panel_bg"], fg="white")
        self.players_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create inner frame for players
        self.player_info_frames = []
        self.player_prop_labels = []
        
        for i in range(4):
            # Player info frame
            pf = tk.Frame(self.players_frame, bg=COLORS["panel_bg"], pady=2)
            pf.pack(fill=tk.X, padx=5)
            
            # Player name and money
            name_label = tk.Label(pf, text="", font=("Helvetica", 10, "bold"),
                                 bg=COLORS["panel_bg"], fg="white", anchor="w")
            name_label.pack(fill=tk.X)
            
            # Properties owned label
            props_label = tk.Label(pf, text="", font=("Helvetica", 8),
                                  bg=COLORS["panel_bg"], fg="#AAA", anchor="w",
                                  wraplength=280, justify=tk.LEFT)
            props_label.pack(fill=tk.X, padx=(15, 0))
            
            self.player_info_frames.append(name_label)
            self.player_prop_labels.append(props_label)
    
    def _create_log_section(self, parent):
        """Game log."""
        frame = tk.LabelFrame(parent, text="📜 Game Log",
                             font=("Helvetica", 12, "bold"),
                             bg=COLORS["panel_bg"], fg="white")
        frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(frame, height=8, font=("Courier", 9),
                               bg="#1a1a2e", fg="#ECF0F1",
                               state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _log(self, msg):
        """Add to game log."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _update_display(self):
        """Update all display elements."""
        player = self.game.current_player
        space = self.game.board.get_space(player.position)
        
        # Current player
        self.current_player_label.config(text=f"{player.token} {player.name}")
        self.money_label.config(text=f"💵 ${player.money:,}")
        self.position_label.config(text=f"📍 {space.name}")
        
        # Players list with properties
        for i, (name_lbl, prop_lbl) in enumerate(zip(self.player_info_frames, self.player_prop_labels)):
            if i < len(self.game.players):
                p = self.game.players[i]
                status = "💀" if p.is_bankrupt else "🔒" if p.in_jail else ""
                arrow = "▶ " if p == player else "   "
                player_color = DEFAULT_PLAYERS[i][2] if i < len(DEFAULT_PLAYERS) else "white"
                
                # Player name line
                name_lbl.config(text=f"{arrow}{p.token} {p.name}: ${p.money:,} {status}")
                if p == player:
                    name_lbl.config(fg=COLORS["active_border"])
                else:
                    name_lbl.config(fg=player_color)
                
                # Properties owned
                if p.properties:
                    prop_names = [prop.name[:10] for prop in p.properties[:6]]
                    more = f" +{len(p.properties) - 6}" if len(p.properties) > 6 else ""
                    prop_lbl.config(text=f"🏠 {', '.join(prop_names)}{more}")
                else:
                    prop_lbl.config(text="No properties")
            else:
                name_lbl.config(text="")
                prop_lbl.config(text="")
        
        # Redraw board
        self._draw_board()
        
        # Update buttons
        if self.waiting_for_buy_decision:
            self.roll_btn.config(state=tk.DISABLED)
            self.buy_btn.config(state=tk.NORMAL)
        else:
            self.roll_btn.config(state=tk.NORMAL)
            self.buy_btn.config(state=tk.DISABLED)
    
    def _update_dice_display(self, roll: DiceRoll):
        """Update dice display with animation."""
        dice_chars = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
        
        # Quick animation
        for _ in range(3):
            d1 = random.choice(dice_chars)
            d2 = random.choice(dice_chars)
            self.dice_label.config(text=f"{d1} {d2}")
            self.root.update()
            self.root.after(50)
        
        # Final result
        self.dice_label.config(text=f"{dice_chars[roll.die1-1]} {dice_chars[roll.die2-1]}")
        
        result_text = f"= {roll.total}"
        if roll.is_doubles:
            result_text += " DOUBLES! 🎉"
            self.dice_result_label.config(fg="#FFD700")
        else:
            self.dice_result_label.config(fg="#AAA")
        self.dice_result_label.config(text=result_text)
    
    def _on_roll(self):
        """Handle dice roll."""
        player = self.game.current_player
        
        if player.in_jail:
            self._handle_jail_roll()
            return
        
        roll = self.game.dice.roll()
        self.game.last_dice_roll = roll
        self._update_dice_display(roll)
        self._log(f"{player.name} rolled {roll.total}")
        
        if self.game.dice.should_go_to_jail:
            self._log(f"Three doubles! {player.name} goes to JAIL!")
            self.game.send_to_jail(player)
            self.roll_btn.config(state=tk.DISABLED)
            self._update_display()
            return
        
        passed_go = player.move(roll.total)
        if passed_go:
            player.receive(200)
            self._log(f"Passed GO! Collected $200")
        
        self._handle_space(player, roll)
        self._update_display()
        
        if roll.is_doubles and not player.in_jail:
            self._log("Doubles! Roll again.")
        else:
            self.roll_btn.config(state=tk.DISABLED)
    
    def _handle_jail_roll(self):
        """Handle jail escape attempt."""
        player = self.game.current_player
        player.jail_turns += 1
        
        roll = self.game.dice.roll()
        self.game.last_dice_roll = roll
        self._update_dice_display(roll)
        
        if roll.is_doubles:
            self._log(f"Doubles! {player.name} escapes jail!")
            player.leave_jail()
            player.move(roll.total)
            self._handle_space(player, roll)
        elif player.jail_turns >= 3:
            self._log(f"Must pay $50 to leave jail")
            player.pay(50)
            player.leave_jail()
            player.move(roll.total)
            self._handle_space(player, roll)
        else:
            self._log(f"No doubles. Still in jail ({player.jail_turns}/3)")
        
        self.roll_btn.config(state=tk.DISABLED)
        self._update_display()
    
    def _handle_space(self, player, roll):
        """Handle landing on a space."""
        space = self.game.board.get_space(player.position)
        self._log(f"Landed on {space.name}")
        
        if isinstance(space, Property):
            if space.owner is None:
                if player.money >= space.price:
                    self.waiting_for_buy_decision = True
                    self.current_property = space
                    self._log(f"Available for ${space.price}")
                    messagebox.showinfo("Property Available",
                                       f"{space.name}\nPrice: ${space.price}\n\nClick 'Buy Property' to purchase.")
            elif space.owner != player and not space.is_mortgaged:
                rent = space.calculate_rent(roll.total)
                self._log(f"Pays ${rent} rent to {space.owner.name}")
                if player.money >= rent:
                    player.pay_to(space.owner, rent)
                else:
                    self._log(f"{player.name} is BANKRUPT!")
                    player.declare_bankruptcy(space.owner)
                    self._check_winner()
        elif isinstance(space, SpecialSpace):
            self._handle_special(player, space)
    
    def _handle_special(self, player, space):
        """Handle special spaces."""
        if space.space_type == SpaceType.GO_TO_JAIL:
            self._log("GO TO JAIL!")
            self.game.send_to_jail(player)
        elif space.space_type == SpaceType.INCOME_TAX:
            tax = min(200, player.money // 10)
            self._log(f"Income Tax: ${tax}")
            player.pay(tax)
        elif space.space_type == SpaceType.LUXURY_TAX:
            self._log("Luxury Tax: $100")
            player.pay(100)
        elif space.space_type == SpaceType.CHANCE:
            card = self.game.chance_deck.draw()
            self._log(f"Chance: {card.description}")
            card.execute(self.game, player)
        elif space.space_type == SpaceType.COMMUNITY_CHEST:
            card = self.game.community_chest_deck.draw()
            self._log(f"Community Chest: {card.description}")
            card.execute(self.game, player)
    
    def _on_buy(self):
        """Buy current property."""
        if self.current_property and self.waiting_for_buy_decision:
            player = self.game.current_player
            prop = self.current_property
            player.pay(prop.price)
            player.add_property(prop)
            self._log(f"Bought {prop.name} for ${prop.price}!")
            self.waiting_for_buy_decision = False
            self.current_property = None
            self._update_display()
    
    def _on_build(self):
        """Build a house."""
        player = self.game.current_player
        buildable = [p for p in player.properties if isinstance(p, Street) and p.can_build()]
        
        if not buildable:
            messagebox.showinfo("Build", "No properties available for building.")
            return
        
        # Simple: build on first available
        prop = buildable[0]
        if player.money >= prop.house_cost and self.game.bank.sell_house():
            prop.build_house()
            player.pay(prop.house_cost)
            self._log(f"Built house on {prop.name}")
            self._update_display()
        else:
            messagebox.showinfo("Build", "Cannot build house.")
    
    def _on_end_turn(self):
        """End current turn."""
        if self.waiting_for_buy_decision:
            self._log("Declined to buy")
            self.waiting_for_buy_decision = False
            self.current_property = None
        
        self.game.dice.reset_doubles()
        self.game.next_turn()
        self.dice_label.config(text="⚀ ⚀")
        self.dice_result_label.config(text="Roll to start!")
        self._log(f"--- {self.game.current_player.name}'s turn ---")
        self._update_display()
    
    def _check_winner(self):
        """Check for winner."""
        active = self.game.active_players
        if len(active) == 1:
            winner = active[0]
            self._log(f"🏆 {winner.name} WINS!")
            messagebox.showinfo("🏆 GAME OVER 🏆", 
                               f"{winner.name} wins the game!\n\nFinal wealth: ${winner.money:,}")
    
    def run(self):
        """Start GUI."""
        self._log("🎲 Welcome to MONOPOLY!")
        self._log(f"--- {self.game.current_player.name}'s turn ---")
        self.root.mainloop()


def main():
    gui = MonopolyGUI(num_players=4)
    gui.run()


if __name__ == "__main__":
    main()
