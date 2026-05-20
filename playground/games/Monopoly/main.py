"""
main.py - Entry point for the Monopoly Pygame application.

Layout:
  Left  (0..690):   Board (668px) + 10px margin
  Right (700..1280): Sidebar (580px) — controls, log, player cards
"""
import pygame
import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox

from engine import MonopolyEngine
from models import Player
from ui_components import (
    Button, LogPanel, PlayerCard, Modal, SectionLabel, DiceDisplay, COLORS, PLAYER_COLORS
)
from board_view import BoardView

SCREEN_W  = 1280
SCREEN_H  = 720
SIDEBAR_X = 690
FPS       = 60

# ──────────────────────────────────────────────────────────────────────────────

def make_font(name, size, bold=False):
    try:
        return pygame.font.SysFont(name, size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size)


def pick_save_path(default_name="大富翁存档.json"):
    root = tk.Tk()
    root.withdraw()
    path = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("存档文件", "*.json")],
        initialfile=default_name,
        title="保存游戏"
    )
    root.destroy()
    return path or None


def pick_load_path():
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
        filetypes=[("存档文件", "*.json")],
        title="读取存档"
    )
    root.destroy()
    return path or None


# ──────────────────────────────────────────────────────────────────────────────

class MonopolyApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("🎩 大富翁 — Python 版")

        self.clock = pygame.time.Clock()

        # 优先选择支持中文的字体
        _cjk_candidates = ["microsoftyahei", "simhei", "simsun", "noto sans cjk sc",
                           "wqy zenhei", "hiragino sans gb", "pingfang sc", "arial unicode ms"]
        _avail = [f.replace(" ", "").lower() for f in pygame.font.get_fonts()]
        _cjk_font = next((c for c in _cjk_candidates if c.replace(" ", "") in _avail), "Arial")

        self.fnt_title  = make_font(_cjk_font, 22, bold=True)
        self.fnt_header = make_font(_cjk_font, 15, bold=True)
        self.fnt_body   = make_font(_cjk_font, 13)
        self.fnt_small  = make_font(_cjk_font, 11)
        self.fnt_tiny   = make_font(_cjk_font, 10)

        # Start with a fresh game
        self.engine = self._new_engine()
        self.board_view = BoardView(x_offset=10, y_offset=10)

        self.modal = None      # active Modal instance or None
        self.ai_delay = 0      # ms timer before AI acts

        self._build_ui()

    def _new_engine(self):
        players = [
            Player("玩家（P1）", is_ai=False),
            Player("机器人（P2）", is_ai=True),
        ]
        return MonopolyEngine(players)

    def _build_ui(self):
        """Build / rebuild the sidebar UI elements."""
        SX = SIDEBAR_X + 16
        W  = SCREEN_W - SIDEBAR_X - 32
        current_y = 12

        self.sections = []

        # ── Player cards ──────────────────────────────
        self.sections.append(SectionLabel(SX, current_y, W, "玩家状态", self.fnt_small))
        current_y += 30
        
        self.player_cards = []
        for i, player in enumerate(self.engine.players):
            pc = PlayerCard(SX, current_y, W, 76, i, self.fnt_body, self.fnt_small)
            self.player_cards.append(pc)
            current_y += 84

        # ── Log panel ─────────────────────────────────
        current_y += 4
        self.log_panel = LogPanel(SX, current_y, W, 210, self.fnt_tiny, title_font=self.fnt_small)
        self.log_panel.add_log("欢迎来到大富翁！")
        self.log_panel.add_log(f"━━ 轮到 {self.engine.current_player().name} ━━")
        current_y += 222

        # ── Dice & Actions ────────────────────────────
        self.sections.append(SectionLabel(SX, current_y, W, "操作与系统", self.fnt_small))
        current_y += 30

        self.dice_display = DiceDisplay(SX, current_y)
        current_y += 44

        BH = 44
        BW = (W - 12) // 2

        self.btn_roll = Button(SX, current_y, W, BH, "投掷骰子", self.fnt_body,
                               COLORS["BtnRoll"], COLORS["BtnRollHov"],
                               self._on_roll, icon="dice")
        current_y += BH + 8

        self.btn_buy  = Button(SX, current_y, BW, BH, "购买地产", self.fnt_body,
                               COLORS["BtnBuy"], COLORS["BtnBuyHov"],
                               self._on_buy, icon="buy")
        self.btn_skip = Button(SX + BW + 12, current_y, BW, BH, "放弃购买", self.fnt_body,
                               COLORS["BtnNeutral"], COLORS["BtnNeutralHov"],
                               self._on_skip, icon="skip")
        current_y += BH + 8

        self.btn_build = Button(SX, current_y, BW, BH, "建造房屋", self.fnt_body,
                                COLORS["BtnBuy"], COLORS["BtnBuyHov"],
                                self._on_build, icon="house")
        self.btn_sell_house = Button(SX + BW + 12, current_y, BW, BH, "出售房屋", self.fnt_body,
                                     COLORS["BtnWarn"], COLORS["BtnWarnHov"],
                                     self._on_sell_house, icon="sell")
        current_y += BH + 8

        self.btn_mortgage = Button(SX, current_y, BW, BH, "抵押地产", self.fnt_body,
                                   COLORS["BtnNeutral"], COLORS["BtnNeutralHov"],
                                   self._on_mortgage, icon="mortgage")
        self.btn_pay_bail = Button(SX + BW + 12, current_y, BW, BH, "保释出狱", self.fnt_body,
                                   COLORS["BtnDanger"], COLORS["BtnDangerHov"],
                                   self._on_pay_bail, icon="jail")
        current_y += BH + 8

        self.btn_save = Button(SX, current_y, BW, BH, "保存进度", self.fnt_body,
                               COLORS["BtnNeutral"], COLORS["BtnNeutralHov"],
                               self._on_save, icon="save")
        self.btn_load = Button(SX + BW + 12, current_y, BW, BH, "读取进度", self.fnt_body,
                               COLORS["BtnNeutral"], COLORS["BtnNeutralHov"],
                               self._on_load, icon="load")

        self.all_buttons = [
            self.btn_roll, self.btn_buy, self.btn_skip,
            self.btn_build, self.btn_sell_house,
            self.btn_mortgage, self.btn_pay_bail,
            self.btn_save, self.btn_load,
        ]

    # ─────────────────────── Button Callbacks ────────────────────────────────

    def _on_roll(self):
        p = self.engine.current_player()
        if not p.is_ai and self.engine.phase == "WAIT_FOR_ROLL":
            self.engine.execute_turn()

    def _on_buy(self):
        p = self.engine.current_player()
        if not p.is_ai and self.engine.phase == "DECIDE_BUY":
            space = self.engine.board[p.position]
            self.engine.buy_property(p, space)

    def _on_skip(self):
        p = self.engine.current_player()
        if not p.is_ai and self.engine.phase == "DECIDE_BUY":
            self.engine.skip_buy(p)

    def _on_build(self):
        """Open a simple modal to select which property to build on."""
        p = self.engine.current_player()
        if p.is_ai or self.engine.phase != "WAIT_FOR_ROLL":
            return
        buildable = [
            prop for prop in p.properties
            if hasattr(prop, "can_build") and prop.can_build(self.engine.board)
            and p.can_afford(prop.build_cost)
        ]
        if not buildable:
            self._show_info("无法建造",
                            "当前没有可建造的地产。\n"
                            "（需要：占齐同色地产、满足均匀建造规则、资金充足）")
            return
        # Build on first eligible for simplicity (could add selection modal later)
        prop = buildable[0]
        self.engine.build_house(p, prop)

    def _on_sell_house(self):
        p = self.engine.current_player()
        if p.is_ai or self.engine.phase != "WAIT_FOR_ROLL":
            return
        sellable = [
            prop for prop in p.properties
            if hasattr(prop, "can_sell_house") and prop.can_sell_house(self.engine.board)
        ]
        if not sellable:
            self._show_info("无法出售", "没有可以出售的房屋。")
            return
        prop = sellable[0]
        self.engine.sell_house(p, prop)

    def _on_mortgage(self):
        p = self.engine.current_player()
        if p.is_ai:
            return
        eligible = [
            prop for prop in p.properties
            if not prop.is_mortgaged and prop.houses == 0
        ]
        if not eligible:
            self._show_info("无法抑押",
                            "没有可抑押的空地产（有房屋的地产需先卖房）。")
            return
        prop = min(eligible, key=lambda x: x.price)
        self.engine.mortgage_property(p, prop)

    def _on_pay_bail(self):
        p = self.engine.current_player()
        if p.is_ai or not p.in_jail:
            return
        self.engine.pay_bail_voluntary()

    def _on_save(self):
        path = pick_save_path()
        if path:
            self.engine.save_game(path)

    def _on_load(self):
        path = pick_load_path()
        if not path:
            return
        try:
            self.engine = MonopolyEngine.load_game(path)
            self._build_ui()
        except Exception as e:
            self._show_info("读档失败", f"无法读取存档：{e}")

    # ─────────────────────── Modal helpers ───────────────────────────────────

    def _show_info(self, title, message):
        self.modal = Modal(
            title, message, SCREEN_W, SCREEN_H,
            self.fnt_header, self.fnt_body,
            btn1_text="确定", btn1_cb=self._close_modal,
        )

    def _close_modal(self):
        self.modal = None

    # ─────────────────────── Button state update ─────────────────────────────

    def _update_button_states(self):
        p = self.engine.current_player()
        is_human = not p.is_ai
        phase = self.engine.phase
        game_over = (phase == "GAME_OVER")

        self.btn_roll.enabled       = is_human and phase == "WAIT_FOR_ROLL" and not game_over
        self.btn_buy.enabled        = is_human and phase == "DECIDE_BUY"
        self.btn_skip.enabled       = is_human and phase == "DECIDE_BUY"
        self.btn_build.enabled      = is_human and phase == "WAIT_FOR_ROLL" and not game_over
        self.btn_sell_house.enabled = is_human and phase == "WAIT_FOR_ROLL" and not game_over
        self.btn_mortgage.enabled   = is_human and not game_over
        self.btn_pay_bail.enabled   = is_human and p.in_jail and not game_over
        self.btn_save.enabled       = not game_over
        self.btn_load.enabled       = True

    # ─────────────────────── AI auto-play ────────────────────────────────────

    def _tick_ai(self, dt):
        if self.engine.current_player().is_ai and self.engine.phase == "WAIT_FOR_ROLL":
            self.ai_delay += dt
            if self.ai_delay >= 900:   # 900 ms delay so the human can read logs
                self.ai_delay = 0
                self.engine.execute_turn()
                # After move, try to build
                p = self.engine.current_player()
                if not p.is_bankrupt:
                    # Run AI build in the next player's idle (they may have rotated)
                    prev = self.engine.players[(self.engine.current_player_index - 1) % len(self.engine.players)]
                    if prev.is_ai:
                        self.engine.ai_build_phase(prev)
        else:
            self.ai_delay = 0

    # ─────────────────────── Sidebar drawing ─────────────────────────────────

    def _draw_sidebar(self):
        s = self.screen
        sx = SIDEBAR_X
        # Sidebar background
        sidebar_rect = pygame.Rect(sx, 0, SCREEN_W - sx, SCREEN_H)
        pygame.draw.rect(s, COLORS["SidebarBg"], sidebar_rect)
        pygame.draw.line(s, COLORS["SidebarBorder"], (sx, 0), (sx, SCREEN_H), 2)

        # Sections
        for sec in self.sections:
            sec.draw(s)

        # Player cards
        for i, pc in enumerate(self.player_cards):
            player = self.engine.players[i]
            is_current = (i == self.engine.current_player_index and
                          self.engine.phase != "GAME_OVER")
            pc.draw(s, player, is_current)

        # Log panel
        self.log_panel.draw(s)

        # Dice display
        d1, d2 = self.engine.last_dice
        self.dice_display.draw(s, d1, d2, self.fnt_body)

        # Buttons
        for btn in self.all_buttons:
            btn.draw(s)

        # 底部状态条
        if self.engine.phase == "GAME_OVER":
            phase_text = f"🏆 获胜者：{self.engine.winner.name if self.engine.winner else '?'}"
        else:
            phase_text = f"阶段：{self.engine.phase}  |  现在轮到：{self.engine.current_player().name}"
        pt = self.fnt_tiny.render(phase_text, True, COLORS["SidebarMuted"])
        s.blit(pt, (sx + 16, SCREEN_H - 20))

    # ─────────────────────── Main loop ───────────────────────────────────────

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                if self.modal and self.modal.visible:
                    self.modal.handle_event(event)
                else:
                    for btn in self.all_buttons:
                        btn.handle_event(event)

            # Drain engine logs → log panel
            while self.engine.logs:
                self.log_panel.add_log(self.engine.logs.pop(0))

            # AI auto-play
            if not (self.modal and self.modal.visible):
                self._tick_ai(dt)

            self._update_button_states()

            # Render
            self.screen.fill(COLORS["SidebarBg"])
            self.board_view.draw_board(self.screen, self.engine)
            self._draw_sidebar()

            if self.modal and self.modal.visible:
                self.modal.draw(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()


def main():
    app = MonopolyApp()
    app.run()


if __name__ == "__main__":
    main()
