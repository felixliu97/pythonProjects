"""
board_view.py - 大富翁棋盘渲染器（美化版）

布局（board_size = 668, corner = 100, cell = 52）：
  下边行: 格0(起点,角) .. 9  → 向左
  左边列: 格10(监狱,角) .. 19 → 向上
  上边行: 格20(免费停车,角) .. 29 → 向右
  右边列: 格30(入狱,角) .. 39 → 向下
"""
import pygame
import math
from ui_components import COLORS, PLAYER_COLORS
from models import PropertySpace, TaxSpace, ActionSpace, CardSpace

# 角格特殊背景
SPACE_BG_OVERRIDE = {
    "GO":             (160, 220, 165),
    "Go To Jail":     (240, 195, 195),
    "Free Parking":   (255, 245, 195),
    "Jail":           (210, 215, 220),
    "Chance":         (255, 225, 140),
    "Community Chest":(185, 235, 255),
    "Tax":            (230, 195, 195),
}

COLOR_BAND = {
    "Brown":     COLORS["Brown"],
    "Light Blue":COLORS["Light Blue"],
    "Pink":      COLORS["Pink"],
    "Orange":    COLORS["Orange"],
    "Red":       COLORS["Red"],
    "Yellow":    COLORS["Yellow"],
    "Green":     COLORS["Green"],
    "Dark Blue": COLORS["Dark Blue"],
}

class BoardView:
    CORNER = 100
    CELL   = 52   # 标准格宽；棋盘 = 100*2 + 52*9 = 668

    def __init__(self, x_offset=10, y_offset=10):
        self.ox = x_offset
        self.oy = y_offset
        self.board_size = self.CORNER * 2 + self.CELL * 9  # = 668
        self.space_rects = []
        self._build_rects()
        self._fonts_ready = False

    # ─── 中文字体查找 ──────────────────────────────────────────────────────────
    _CJK_FONTS = ["microsoftyahei", "simhei", "simsun", "noto sans cjk sc",
                  "wqy zenhei", "hiragino sans gb", "pingfang sc", "arial unicode ms"]

    @classmethod
    def _find_cjk_font(cls):
        available = [f.lower().replace(" ", "") for f in pygame.font.get_fonts()]
        for c in cls._CJK_FONTS:
            if c.replace(" ", "") in available:
                return c
        return "Arial"

    def _init_fonts(self):
        if self._fonts_ready:
            return
        cjk = self._find_cjk_font()
        self.fnt_tiny   = pygame.font.SysFont(cjk,  8)
        self.fnt_small  = pygame.font.SysFont(cjk, 10, bold=True)
        self.fnt_corner = pygame.font.SysFont(cjk, 11, bold=True)
        self.fnt_price  = pygame.font.SysFont(cjk,  9)
        self.fnt_corner_big = pygame.font.SysFont(cjk, 14, bold=True)
        self._fonts_ready = True

    # ─── 格子矩形布局 ─────────────────────────────────────────────────────────
    def _build_rects(self):
        C = self.CORNER; S = self.CELL; B = self.board_size
        for i in range(40):
            if i == 0:
                r = pygame.Rect(B - C, B - C, C, C)
            elif 1 <= i <= 9:
                r = pygame.Rect(B - C - i * S, B - C, S, C)
            elif i == 10:
                r = pygame.Rect(0, B - C, C, C)
            elif 11 <= i <= 19:
                r = pygame.Rect(0, B - C - (i - 10) * S, C, S)
            elif i == 20:
                r = pygame.Rect(0, 0, C, C)
            elif 21 <= i <= 29:
                r = pygame.Rect(C + (i - 21) * S, 0, S, C)
            elif i == 30:
                r = pygame.Rect(B - C, 0, C, C)
            elif 31 <= i <= 39:
                r = pygame.Rect(B - C, C + (i - 31) * S, C, S)
            r.x += self.ox
            r.y += self.oy
            self.space_rects.append(r)

    # ─── 主绘制入口 ───────────────────────────────────────────────────────────
    def draw_board(self, surface, engine):
        self._init_fonts()
        B = self.board_size

        # 棋盘阴影
        shadow = pygame.Rect(self.ox + 5, self.oy + 5, B, B)
        sh_surf = pygame.Surface((B, B), pygame.SRCALPHA)
        sh_surf.fill((0, 0, 0, 60))
        surface.blit(sh_surf, shadow)

        # 棋盘底色（带细腻纹理感）
        board_rect = pygame.Rect(self.ox, self.oy, B, B)
        pygame.draw.rect(surface, COLORS["BoardBg"], board_rect)

        # 棋盘内部网格线（淡）
        grid_color = (180, 215, 180)
        for x in range(self.ox, self.ox + B, 20):
            pygame.draw.line(surface, grid_color, (x, self.oy), (x, self.oy + B), 1)
        for y in range(self.oy, self.oy + B, 20):
            pygame.draw.line(surface, grid_color, (self.ox, y), (self.ox + B, y), 1)

        pygame.draw.rect(surface, COLORS["Border"], board_rect, 3)

        # 中央区域
        cx = self.ox + self.CORNER
        cy = self.oy + self.CORNER
        cw = ch = B - 2 * self.CORNER
        center_rect = pygame.Rect(cx, cy, cw, ch)
        self._draw_center(surface, center_rect)

        # 绘制各格
        for i, space in enumerate(engine.board):
            self._draw_space(surface, i, space, engine)

        # 绘制棋子
        self._draw_tokens(surface, engine)

    def _draw_center(self, surface, rect):
        """棋盘中央装饰区。"""
        # 渐变绿色背景
        pygame.draw.rect(surface, (158, 200, 158), rect)

        # 棋盘图案（四角装饰菱形）
        for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            px = rect.centerx + dx * (rect.w // 3)
            py = rect.centery + dy * (rect.h // 3)
            size = 12
            pts = [(px, py - size), (px + size, py),
                   (px, py + size), (px - size, py)]
            pygame.draw.polygon(surface, (140, 182, 140), pts)

        # 外框
        pygame.draw.rect(surface, (90, 140, 90), rect, 2)

        # 内框装饰线
        inner = rect.inflate(-20, -20)
        pygame.draw.rect(surface, (110, 160, 110), inner, 1)

        cjk = self._find_cjk_font()
        fnt_big = pygame.font.SysFont(cjk, 38, bold=True)
        fnt_sub = pygame.font.SysFont(cjk, 13)
        fnt_tiny = pygame.font.SysFont(cjk, 10)

        # 主标题（带阴影）
        for off in [(2, 2), (0, 0)]:
            col = (60, 100, 60) if off == (2, 2) else COLORS["Red"]
            title = fnt_big.render("大  富  翁", True, col)
            tr = title.get_rect(center=(rect.centerx + off[0], rect.centery - 18 + off[1]))
            surface.blit(title, tr)

        # 装饰横线
        lw = rect.width - 50
        lx = rect.x + 25
        line_y1 = rect.centery - 42
        line_y2 = rect.centery + 16
        pygame.draw.line(surface, (90, 140, 90), (lx, line_y1), (lx + lw, line_y1), 2)
        pygame.draw.line(surface, (90, 140, 90), (lx, line_y2), (lx + lw, line_y2), 2)
        # 线段端点小菱形
        for lx2 in [lx, lx + lw]:
            for ly2 in [line_y1, line_y2]:
                pts = [(lx2, ly2 - 4), (lx2 + 4, ly2),
                       (lx2, ly2 + 4), (lx2 - 4, ly2)]
                pygame.draw.polygon(surface, (90, 140, 90), pts)

        # 副标题
        sub = fnt_sub.render("经典地产交易游戏", True, (80, 120, 80))
        sr = sub.get_rect(center=(rect.centerx, rect.centery + 32))
        surface.blit(sub, sr)

        # 版本标注
        ver = fnt_tiny.render("Python Edition", True, (110, 150, 110))
        vr = ver.get_rect(center=(rect.centerx, rect.centery + 50))
        surface.blit(ver, vr)

    # ─── 单格绘制 ─────────────────────────────────────────────────────────────
    def _draw_space(self, surface, idx, space, engine):
        rect = self.space_rects[idx]
        BAND = 18

        # 背景色
        bg = COLORS["SpaceBg"]
        if isinstance(space, ActionSpace):
            bg = SPACE_BG_OVERRIDE.get(space.action_type, COLORS["SpaceBg"])
        elif isinstance(space, CardSpace):
            bg = SPACE_BG_OVERRIDE.get(space.card_type, COLORS["SpaceBg"])
        elif isinstance(space, TaxSpace):
            bg = SPACE_BG_OVERRIDE["Tax"]

        pygame.draw.rect(surface, bg, rect)
        pygame.draw.rect(surface, COLORS["Border"], rect, 1)

        # 彩色标签条
        if isinstance(space, PropertySpace) and space.color in COLOR_BAND:
            band_color = COLOR_BAND[space.color]
            if idx in range(1, 10):
                band = pygame.Rect(rect.x, rect.y, rect.w, BAND)
            elif idx in range(11, 20):
                band = pygame.Rect(rect.right - BAND, rect.y, BAND, rect.h)
            elif idx in range(21, 30):
                band = pygame.Rect(rect.x, rect.bottom - BAND, rect.w, BAND)
            else:
                band = pygame.Rect(rect.x, rect.y, BAND, rect.h)

            # 抵押：灰色覆盖
            if space.is_mortgaged:
                pygame.draw.rect(surface, (140, 140, 140), band)
                # 斜线标记
                pygame.draw.line(surface, (100, 100, 100),
                                 (band.x, band.y), (band.right, band.bottom), 2)
                pygame.draw.line(surface, (100, 100, 100),
                                 (band.right, band.y), (band.x, band.bottom), 2)
            else:
                pygame.draw.rect(surface, band_color, band)
                # 高光
                hi = pygame.Surface((band.w, max(4, band.h // 3)), pygame.SRCALPHA)
                hi.fill((255, 255, 255, 50))
                surface.blit(hi, band)

            pygame.draw.rect(surface, COLORS["Border"], band, 1)

            # 建筑物
            if space.houses > 0:
                self._draw_buildings(surface, idx, space, band)

        # 文字
        self._draw_space_text(surface, idx, space, rect, BAND)

        # 所有者圆点
        if isinstance(space, PropertySpace) and space.owner:
            oi = engine.players.index(space.owner)
            col = PLAYER_COLORS[oi % len(PLAYER_COLORS)]
            pygame.draw.circle(surface, col, (rect.x + 9, rect.y + 8), 6)
            pygame.draw.circle(surface, COLORS["White"], (rect.x + 9, rect.y + 8), 6, 1)

        # 价格标签
        if isinstance(space, PropertySpace) and space.owner is None:
            ps = self.fnt_price.render(f"¥{space.price}", True, (80, 80, 90))
            if idx in range(1, 10):
                pr = ps.get_rect(centerx=rect.centerx, bottom=rect.bottom - 2)
            elif idx in range(11, 20):
                pr = ps.get_rect(centerx=rect.centerx, bottom=rect.bottom - 2)
            elif idx in range(21, 30):
                pr = ps.get_rect(centerx=rect.centerx, top=rect.top + 2)
            else:
                pr = ps.get_rect(centerx=rect.centerx, top=rect.top + 2)
            surface.blit(ps, pr)

    def _draw_space_text(self, surface, idx, space, rect, band):
        is_corner = idx in [0, 10, 20, 30]
        fnt = self.fnt_corner if is_corner else self.fnt_tiny

        name = space.name
        abbrevs = {
            "北卡罗来纳大道": "北卡\n大道",
            "宾夕法尼亚铁路": "宾州\n铁路",
            "宾夕法尼亚大道": "宾州\n大道",
            "圣查尔斯广场":   "圣查\n广场",
            "圣詹姆斯广场":   "圣詹\n广场",
            "监狱/探监":       "监狱\n探监",
            "免费停车":        "免费\n停车",
            "入狱":            "入\n狱",
        }
        name = abbrevs.get(name, name)
        lines = name.split("\n") if "\n" in name else self._wrap(
            name, fnt,
            rect.width - 4 if idx not in range(11, 20) and idx not in range(31, 40)
            else rect.height - band - 4
        )

        # 角格特殊图标
        if is_corner:
            self._draw_corner(surface, idx, space, rect, lines)
        elif idx in range(11, 20):
            self._draw_rotated_text(surface, lines, fnt, rect, "right")
        elif idx in range(31, 40):
            self._draw_rotated_text(surface, lines, fnt, rect, "left")
        elif idx in range(1, 10):
            y = rect.y + band + 3
            for ln in lines:
                t = fnt.render(ln, True, COLORS["Black"])
                tr = t.get_rect(centerx=rect.centerx, top=y)
                surface.blit(t, tr)
                y += fnt.get_height() + 1
        else:
            y = rect.y + 2
            for ln in lines:
                t = fnt.render(ln, True, COLORS["Black"])
                tr = t.get_rect(centerx=rect.centerx, top=y)
                surface.blit(t, tr)
                y += fnt.get_height() + 1

    def _draw_corner(self, surface, idx, space, rect, lines):
        """角格特殊绘制：加图标和大字。"""
        cx, cy = rect.centerx, rect.centery
        fnt = self.fnt_corner

        if idx == 0:  # 起点
            # 绿色大箭头
            arrow_pts = [(cx + 18, cy - 8), (cx + 28, cy), (cx + 18, cy + 8)]
            pygame.draw.polygon(surface, (30, 160, 75), arrow_pts)
            pygame.draw.polygon(surface, (20, 130, 60), arrow_pts, 2)
            # 文字
            t = self.fnt_corner_big.render("起  点", True, (20, 120, 55))
            surface.blit(t, t.get_rect(center=(cx - 5, cy)))
            # 金额
            m = self.fnt_price.render("领 ¥200", True, (180, 60, 60))
            surface.blit(m, m.get_rect(center=(cx, cy + 22)))

        elif idx == 10:  # 监狱/探监
            # 灰色条纹背景
            stripe_surf = pygame.Surface((rect.w // 2, rect.h), pygame.SRCALPHA)
            for i in range(0, rect.h, 6):
                stripe_surf.fill((0, 0, 0, 20), pygame.Rect(0, i, rect.w // 2, 3))
            surface.blit(stripe_surf, (rect.x, rect.y))
            # 铁窗图形
            bar_x = rect.x + rect.w // 2 + 4
            bar_y = rect.y + 10
            bar_h = rect.h - 20
            for bx in range(bar_x, bar_x + 45, 8):
                pygame.draw.line(surface, (90, 90, 100), (bx, bar_y), (bx, bar_y + bar_h), 2)
            pygame.draw.line(surface, (90, 90, 100), (bar_x, bar_y + bar_h // 2),
                             (bar_x + 45, bar_y + bar_h // 2), 2)
            # 文字
            t1 = fnt.render("监狱", True, (80, 80, 90))
            t2 = self.fnt_price.render("探  监", True, (100, 100, 110))
            surface.blit(t1, t1.get_rect(center=(rect.x + rect.w // 4, cy - 8)))
            surface.blit(t2, t2.get_rect(center=(rect.x + rect.w // 4, cy + 10)))

        elif idx == 20:  # 免费停车
            # 停车P图标
            pygame.draw.circle(surface, (255, 230, 80), (cx, cy - 8), 22)
            pygame.draw.circle(surface, (200, 170, 0), (cx, cy - 8), 22, 2)
            p_fnt = pygame.font.SysFont(self._find_cjk_font(), 26, bold=True)
            p = p_fnt.render("P", True, (160, 100, 0))
            surface.blit(p, p.get_rect(center=(cx, cy - 8)))
            t = self.fnt_price.render("免费停车", True, (120, 80, 0))
            surface.blit(t, t.get_rect(center=(cx, cy + 20)))

        elif idx == 30:  # 入狱
            # 红色感叹号背景
            pygame.draw.circle(surface, (220, 60, 60), (cx, cy - 10), 28)
            pygame.draw.circle(surface, (180, 40, 40), (cx, cy - 10), 28, 2)
            ex_fnt = pygame.font.SysFont(self._find_cjk_font(), 28, bold=True)
            ex = ex_fnt.render("!", True, (255, 255, 255))
            surface.blit(ex, ex.get_rect(center=(cx, cy - 10)))
            t = self.fnt_price.render("直接入狱", True, (180, 40, 40))
            surface.blit(t, t.get_rect(center=(cx, cy + 24)))

    def _draw_rotated_text(self, surface, lines, fnt, rect, direction):
        angle = -90 if direction == "right" else 90
        combined_h = sum(fnt.get_height() + 1 for _ in lines)
        start_x = rect.centerx - combined_h // 2 + fnt.get_height() // 2
        for ln in lines:
            raw = fnt.render(ln, True, COLORS["Black"])
            rotated = pygame.transform.rotate(raw, angle)
            rr = rotated.get_rect(center=(start_x, rect.centery))
            surface.blit(rotated, rr)
            start_x += fnt.get_height() + 2

    def _wrap(self, text, fnt, max_w):
        """逐字符换行（支持中文）。"""
        lines, current = [], ""
        for ch in text:
            test = current + ch
            if fnt.size(test)[0] <= max(max_w, 16):
                current = test
            else:
                if current:
                    lines.append(current)
                current = ch
        if current:
            lines.append(current)
        return lines or [text]

    # ─── 建筑物绘制 ───────────────────────────────────────────────────────────
    def _draw_buildings(self, surface, idx, space, band_rect):
        count = space.houses
        is_hotel = (count == 5)
        n = 1 if is_hotel else count
        house_col = (30, 180, 75)
        hotel_col = (210, 40, 40)

        size = min(10, (band_rect.w - 4) // max(n, 1)) if band_rect.w >= band_rect.h \
               else min(10, (band_rect.h - 4) // max(n, 1))
        size = max(size, 5)

        if band_rect.w >= band_rect.h:
            total_w = n * (size + 2) - 2
            sx = band_rect.centerx - total_w // 2
            for k in range(n):
                x = sx + k * (size + 2)
                y = band_rect.centery - size // 2
                if is_hotel:
                    pygame.draw.rect(surface, hotel_col, (x, y, size, size))
                    # 屋顶三角
                    tri = [(x, y), (x + size, y), (x + size // 2, y - size // 2)]
                    pygame.draw.polygon(surface, (170, 30, 30), tri)
                else:
                    pygame.draw.rect(surface, house_col, (x, y, size, size))
                    tri = [(x, y), (x + size, y), (x + size // 2, y - size // 3)]
                    pygame.draw.polygon(surface, (20, 140, 55), tri)
        else:
            total_h = n * (size + 2) - 2
            sy = band_rect.centery - total_h // 2
            for k in range(n):
                x = band_rect.centerx - size // 2
                y = sy + k * (size + 2)
                if is_hotel:
                    pygame.draw.rect(surface, hotel_col, (x, y, size, size))
                else:
                    pygame.draw.rect(surface, house_col, (x, y, size, size))

    # ─── 玩家棋子 ─────────────────────────────────────────────────────────────
    def _draw_tokens(self, surface, engine):
        pos_groups = {}
        for idx, player in enumerate(engine.players):
            if not player.is_bankrupt:
                pos_groups.setdefault(player.position, []).append(idx)

        for pos, idxs in pos_groups.items():
            rect = self.space_rects[pos]
            offsets = self._token_offsets(len(idxs), rect)
            for i, player_idx in enumerate(idxs):
                px, py = offsets[i]
                col = PLAYER_COLORS[player_idx % len(PLAYER_COLORS)]
                radius = 11
                # 阴影
                pygame.draw.circle(surface, (0, 0, 0, 80), (px + 1, py + 2), radius)
                # 主圆
                pygame.draw.circle(surface, col, (px, py), radius)
                # 高光
                pygame.draw.circle(surface, tuple(min(255, c + 60) for c in col),
                                   (px - 3, py - 3), radius // 3)
                # 白色外圈
                pygame.draw.circle(surface, COLORS["White"], (px, py), radius, 2)
                # 编号
                num = self.fnt_small.render(str(player_idx + 1), True, COLORS["White"])
                nr = num.get_rect(center=(px, py))
                surface.blit(num, nr)

    def _token_offsets(self, n, rect):
        cx, cy = rect.centerx, rect.centery
        if n == 1:
            return [(cx, cy)]
        elif n == 2:
            return [(cx - 9, cy), (cx + 9, cy)]
        elif n == 3:
            return [(cx - 10, cy + 6), (cx + 10, cy + 6), (cx, cy - 8)]
        else:
            return [(cx - 10, cy - 8), (cx + 10, cy - 8),
                    (cx - 10, cy + 8), (cx + 10, cy + 8)]
