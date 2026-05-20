"""
ui_components.py - 大富翁游戏 UI 设计系统（全中文 + 内嵌图标，无 Emoji 依赖）
"""
import pygame
import math

# ─────────────────────────── 调色板 ──────────────────────────────────────────
COLORS = {
    # 地产颜色条
    "Brown":          (139,  87,  42),
    "Light Blue":     (100, 195, 240),
    "Pink":           (215,  60, 130),
    "Orange":         (245, 145,  30),
    "Red":            (220,  40,  40),
    "Yellow":         (250, 208,   0),
    "Green":          (30,  160,  75),
    "Dark Blue":      (25,   75, 175),
    "Station":        (80,   80,  85),
    "Utility":        (155, 125,  65),

    # 棋盘
    "BoardBg":        (195, 228, 195),
    "CenterBg":       (165, 208, 165),
    "SpaceBg":        (252, 252, 248),
    "Border":         (35,  35,  35),
    "BorderLight":    (150, 150, 150),

    # 深色侧边栏主题
    "SidebarBg":      (14,  20,  34),
    "SidebarPanel":   (22,  32,  52),
    "SidebarPanel2":  (30,  42,  68),
    "SidebarBorder":  (45,  62,  98),
    "SidebarText":    (205, 220, 245),
    "SidebarMuted":   (95, 115, 155),
    "SidebarAccent":  (75, 145, 255),
    "SidebarAccent2": (50, 200, 160),

    # 按钮系统
    "BtnRoll":        (65,  140, 245),
    "BtnRollHov":     (90,  165, 255),
    "BtnBuy":         (40,  168,  85),
    "BtnBuyHov":      (55,  195, 105),
    "BtnDanger":      (205,  55,  55),
    "BtnDangerHov":   (235,  75,  75),
    "BtnNeutral":     (52,   68, 102),
    "BtnNeutralHov":  (70,   90, 130),
    "BtnWarn":        (195, 125,  20),
    "BtnWarnHov":     (225, 150,  35),
    "BtnDisabled":    (35,  46,  68),
    "BtnText":        (240, 246, 255),
    "BtnTextDis":     (80,   95, 125),

    # 杂项
    "White":          (255, 255, 255),
    "Black":          (0,   0,   0),
    "Gold":           (255, 198,  10),
    "GoldDark":       (200, 155,   0),
    "LogEntry":       (215, 232, 255),
    "LogAlt":         (190, 210, 245),
    "LogTimestamp":   (80, 120, 180),
    "Highlight":      (255, 240, 100),
}

PLAYER_COLORS = [
    (240,  70,  70),   # P1 红
    (70,  130, 250),   # P2 蓝
    (70,  205, 100),   # P3 绿
    (250, 205,  50),   # P4 黄
    (215,  75, 215),   # P5 紫
    (50,  215, 215),   # P6 青
    (250, 135,  50),   # P7 橙
    (175, 175, 180),   # P8 银
]

# ─────────────────────────── 内嵌图标绘制 ────────────────────────────────────
def draw_icon(surface, icon_name, cx, cy, size, color=(255, 255, 255), enabled=True):
    """
    在 (cx, cy) 为圆心、size 为半径范围内绘制指定图标。
    所有图标均为纯 Pygame 绘图，无需外部文件，完美支持中文字体环境。
    """
    alpha = 255 if enabled else 120
    c = (*color[:3],)

    if icon_name == "dice":
        # 骰子：白色圆角方块 + 红色点
        r = size // 2
        rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
        pygame.draw.rect(surface, (240, 240, 240), rect, border_radius=4)
        pygame.draw.rect(surface, (180, 180, 180), rect, 1, border_radius=4)
        dot_r = max(2, size // 8)
        dot_color = (200, 30, 30)
        # 4点面
        for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            pygame.draw.circle(surface, dot_color,
                               (cx + dx * (r // 2), cy + dy * (r // 2)), dot_r)

    elif icon_name == "buy":
        # 绿色圆形 + 白色勾
        pygame.draw.circle(surface, (40, 175, 85), (cx, cy), size)
        pygame.draw.circle(surface, (60, 200, 105), (cx, cy), size, 2)
        s = size // 2
        pts = [(cx - s + 2, cy), (cx - s//3, cy + s//2), (cx + s, cy - s//2)]
        if len(pts) >= 2:
            pygame.draw.lines(surface, (255, 255, 255), False, pts, max(2, size // 5))

    elif icon_name == "skip":
        # 两个灰色右三角
        s = size // 2
        for ox in [-s//2, s//3]:
            tri = [(cx + ox, cy - s), (cx + ox + s, cy), (cx + ox, cy + s)]
            pygame.draw.polygon(surface, (160, 175, 200), tri)

    elif icon_name == "house":
        # 小屋：三角屋顶 + 方形主体
        s = size // 2
        # 屋顶
        roof = [(cx, cy - s), (cx - s, cy), (cx + s, cy)]
        pygame.draw.polygon(surface, (200, 60, 60), roof)
        # 主体
        body = pygame.Rect(cx - s + 3, cy, (s - 3) * 2, s)
        pygame.draw.rect(surface, (240, 220, 180), body)
        # 门
        door = pygame.Rect(cx - 3, cy + s // 3, 6, s - s // 3)
        pygame.draw.rect(surface, (120, 80, 40), door)

    elif icon_name == "sell":
        # 锤子
        s = size // 2
        # 锤头
        head = pygame.Rect(cx - s // 2, cy - s, s, s // 2)
        pygame.draw.rect(surface, (220, 150, 40), head, border_radius=2)
        # 把手
        pygame.draw.line(surface, (160, 100, 40),
                         (cx + s // 4, cy - s // 2), (cx + s, cy + s), max(2, s // 3))

    elif icon_name == "mortgage":
        # 柱廊建筑（银行）
        s = size // 2
        # 底座
        pygame.draw.rect(surface, (220, 185, 50),
                         pygame.Rect(cx - s, cy + s // 2, s * 2, s // 3))
        # 柱子
        for i in range(3):
            x = cx - s + s // 2 * i + s // 4
            pygame.draw.rect(surface, (230, 195, 60),
                             pygame.Rect(x - 2, cy - s // 2, 5, s))
        # 屋顶三角
        roof = [(cx - s, cy - s // 2), (cx, cy - s), (cx + s, cy - s // 2)]
        pygame.draw.polygon(surface, (220, 185, 50), roof)

    elif icon_name == "jail":
        # 铁窗格子
        s = size // 2
        # 外框
        pygame.draw.rect(surface, (180, 50, 50),
                         pygame.Rect(cx - s, cy - s, s * 2, s * 2), 2)
        # 竖条
        for i in range(3):
            x = cx - s + (i + 1) * (s * 2 // 4)
            pygame.draw.line(surface, (200, 60, 60), (x, cy - s + 2), (x, cy + s - 2), 2)
        # 横条
        pygame.draw.line(surface, (200, 60, 60), (cx - s + 2, cy), (cx + s - 2, cy), 2)

    elif icon_name == "save":
        # 软盘图标
        s = size // 2
        rect = pygame.Rect(cx - s, cy - s, s * 2, s * 2)
        pygame.draw.rect(surface, (65, 130, 240), rect, border_radius=3)
        # 标签区
        label = pygame.Rect(cx - s + 3, cy - s + 3, s * 2 - 6, s - 2)
        pygame.draw.rect(surface, (220, 235, 255), label)
        # 写保护滑块
        slider = pygame.Rect(cx + 2, cy - s + 4, s // 2, s - 4)
        pygame.draw.rect(surface, (140, 165, 220), slider)
        # 底部存储区
        bottom = pygame.Rect(cx - s + 3, cy + 2, s * 2 - 6, s - 4)
        pygame.draw.rect(surface, (40, 100, 200), bottom, border_radius=2)

    elif icon_name == "load":
        # 文件夹图标
        s = size // 2
        # 文件夹体
        body = pygame.Rect(cx - s, cy - s // 3, s * 2, s + s // 3)
        pygame.draw.rect(surface, (240, 165, 50), body, border_radius=3)
        # 文件夹 tab
        tab = pygame.Rect(cx - s, cy - s // 3 - s // 3, s, s // 3)
        pygame.draw.rect(surface, (255, 185, 65), tab,
                         border_top_left_radius=3, border_top_right_radius=3)
        # 内部文件线条
        for i in range(2):
            yy = cy + i * (s // 3)
            pygame.draw.line(surface, (255, 210, 130),
                             (cx - s + 6, yy), (cx + s - 6, yy), 1)

# ─────────────────────────── 按钮组件 ────────────────────────────────────────
class Button:
    def __init__(self, x, y, w, h, text, font,
                 color_normal=None, color_hover=None,
                 on_click=None, radius=10, icon=None):
        self.rect     = pygame.Rect(x, y, w, h)
        self.text     = text
        self.font     = font
        self.color_normal = color_normal or COLORS["BtnRoll"]
        self.color_hover  = color_hover  or COLORS["BtnRollHov"]
        self.on_click = on_click
        self.radius   = radius
        self.icon     = icon           # str key for draw_icon, or None
        self.is_hovered = False
        self.enabled  = True
        self._press_alpha = 0          # simple press flash

    def draw(self, surface):
        if not self.enabled:
            base  = COLORS["BtnDisabled"]
            tcolor = COLORS["BtnTextDis"]
        elif self.is_hovered:
            base  = self.color_hover
            tcolor = COLORS["BtnText"]
        else:
            base  = self.color_normal
            tcolor = COLORS["BtnText"]

        # Shadow
        shadow_rect = pygame.Rect(self.rect.x + 2, self.rect.y + 3,
                                  self.rect.w, self.rect.h)
        shadow_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 60), shadow_surf.get_rect(),
                         border_radius=self.radius)
        surface.blit(shadow_surf, shadow_rect)

        # Body
        pygame.draw.rect(surface, base, self.rect, border_radius=self.radius)

        # Top-edge highlight (glass feel)
        if self.enabled:
            hi_rect = pygame.Rect(self.rect.x + 2, self.rect.y + 1,
                                  self.rect.w - 4, self.rect.h // 3)
            hi_surf = pygame.Surface((hi_rect.w, hi_rect.h), pygame.SRCALPHA)
            hi_surf.fill((255, 255, 255, 25))
            surface.blit(hi_surf, hi_rect)

        # Border
        lighter = tuple(min(255, c + 50) for c in base)
        pygame.draw.rect(surface, lighter, self.rect, 1, border_radius=self.radius)

        # Icon + text layout
        icon_size = self.rect.h // 3
        if self.icon:
            icon_cx = self.rect.x + icon_size + 6
            txt = self.font.render(self.text, True, tcolor)
            total_w = icon_size * 2 + 4 + txt.get_width()
            text_x  = self.rect.centerx - total_w // 2 + icon_size * 2 + 4
            text_y  = self.rect.centery - txt.get_height() // 2
            icon_cx2 = self.rect.centerx - total_w // 2 + icon_size
            draw_icon(surface, self.icon, icon_cx2, self.rect.centery,
                      icon_size, enabled=self.enabled)
            surface.blit(txt, (text_x, text_y))
        else:
            txt = self.font.render(self.text, True, tcolor)
            tr  = txt.get_rect(center=self.rect.center)
            surface.blit(txt, tr)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos) and self.enabled
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.enabled and self.rect.collidepoint(event.pos):
                if self.on_click:
                    self.on_click()
                return True
        return False

# ─────────────────────────── 日志面板 ────────────────────────────────────────
class LogPanel:
    def __init__(self, x, y, w, h, font, title_font=None):
        self.rect        = pygame.Rect(x, y, w, h)
        self.font        = font
        self.title_font  = title_font or font
        self.logs        = []
        self.line_height = font.get_height() + 3
        self.max_lines   = (h - 28) // self.line_height

    def add_log(self, text):
        """自动换行并存入日志。"""
        max_w = self.rect.width - 18
        # 按字符逐步拼行（中文无法按空格分词）
        current = ""
        for ch in text:
            test = current + ch
            if self.font.size(test)[0] <= max_w:
                current = test
            else:
                if current:
                    self.logs.append(current)
                current = ch
        if current:
            self.logs.append(current)
        while len(self.logs) > self.max_lines * 2:
            self.logs.pop(0)

    def draw(self, surface):
        # 面板背景
        pygame.draw.rect(surface, COLORS["SidebarPanel"], self.rect, border_radius=10)
        # 顶部标题条
        title_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.w, 22)
        pygame.draw.rect(surface, COLORS["SidebarPanel2"], title_rect,
                         border_top_left_radius=10, border_top_right_radius=10)
        # 标题文字
        t = self.title_font.render("游戏日志", True, COLORS["SidebarAccent"])
        surface.blit(t, (self.rect.x + 10, self.rect.y + 3))

        # 边框
        pygame.draw.rect(surface, COLORS["SidebarBorder"], self.rect, 1, border_radius=10)

        # 日志条目
        visible_start = max(0, len(self.logs) - self.max_lines)
        y = self.rect.y + 26
        for i, log in enumerate(self.logs[visible_start:]):
            age = i / max(self.max_lines - 1, 1)
            # 新消息更亮
            alpha_v = int(180 + age * 75)
            r, g, b = COLORS["LogEntry"]
            r2, g2, b2 = COLORS["LogAlt"]
            col = (
                int(r2 + (r - r2) * age),
                int(g2 + (g - g2) * age),
                int(b2 + (b - b2) * age),
            )
            # 最后一条高亮
            if i == len(self.logs[visible_start:]) - 1:
                hi = pygame.Rect(self.rect.x + 2, y - 1, self.rect.w - 4,
                                 self.line_height + 1)
                pygame.draw.rect(surface, (40, 55, 90), hi)
                col = COLORS["Highlight"]
            txt = self.font.render(log, True, col)
            surface.blit(txt, (self.rect.x + 10, y))
            y += self.line_height

# ─────────────────────────── 玩家信息卡 ──────────────────────────────────────
class PlayerCard:
    """显示玩家姓名、资金、地产数量。"""
    def __init__(self, x, y, w, h, player_idx, font_name, font_stat):
        self.rect       = pygame.Rect(x, y, w, h)
        self.player_idx = player_idx
        self.font_name  = font_name
        self.font_stat  = font_stat

    def draw(self, surface, player, is_current):
        color  = PLAYER_COLORS[self.player_idx % len(PLAYER_COLORS)]
        bg     = COLORS["SidebarPanel"]
        border = color if is_current else COLORS["SidebarBorder"]
        bw     = 2 if is_current else 1

        # 背景
        pygame.draw.rect(surface, bg, self.rect, border_radius=10)

        # 活跃玩家发光效果
        if is_current:
            glow = pygame.Surface((self.rect.w + 4, self.rect.h + 4), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*color, 40),
                             glow.get_rect(), border_radius=12)
            surface.blit(glow, (self.rect.x - 2, self.rect.y - 2))

        # 左侧彩色宽条
        stripe_w = 7
        stripe = pygame.Rect(self.rect.x, self.rect.y, stripe_w, self.rect.h)
        pygame.draw.rect(surface, color, stripe,
                         border_top_left_radius=10, border_bottom_left_radius=10)

        # 玩家头像圆圈
        avatar_r = 18
        avatar_x = self.rect.x + stripe_w + avatar_r + 6
        avatar_y = self.rect.centery
        pygame.draw.circle(surface, color, (avatar_x, avatar_y), avatar_r)
        pygame.draw.circle(surface, COLORS["White"], (avatar_x, avatar_y), avatar_r, 2)
        # 玩家编号
        num_fnt = pygame.font.SysFont(None, 22)
        num_s = num_fnt.render(str(self.player_idx + 1), True, COLORS["White"])
        nr = num_s.get_rect(center=(avatar_x, avatar_y))
        surface.blit(num_s, nr)

        # 文字区域起点
        tx = avatar_x + avatar_r + 10

        if player.is_bankrupt:
            t = self.font_name.render(f"[淘汰] {player.name}", True, (150, 70, 70))
            surface.blit(t, (tx, self.rect.y + (self.rect.h - t.get_height()) // 2))
        else:
            # 名字
            prefix = "▶ " if is_current else ""
            name_c = color if is_current else COLORS["SidebarText"]
            nt = self.font_name.render(f"{prefix}{player.name}", True, name_c)
            surface.blit(nt, (tx, self.rect.y + 8))

            # 资金（带小钱币图标）
            money_str = f"${player.money:,}"
            mt = self.font_stat.render(money_str, True, COLORS["Gold"])
            surface.blit(mt, (tx, self.rect.y + 28))
            # 小金币点缀
            pygame.draw.circle(surface, COLORS["Gold"],
                                (tx - 8, self.rect.y + 28 + mt.get_height() // 2), 4)

            # 地产数
            prop_str = f"{len(player.properties)} 个地产"
            pt = self.font_stat.render(prop_str, True, COLORS["SidebarMuted"])
            surface.blit(pt, (tx + mt.get_width() + 14, self.rect.y + 28))

            # 监狱状态标记
            if player.in_jail:
                jail_t = self.font_stat.render("[在狱]", True, (220, 100, 50))
                surface.blit(jail_t, (tx + mt.get_width() + 14, self.rect.y + 8))

        # 外框
        pygame.draw.rect(surface, border, self.rect, bw, border_radius=10)

# ─────────────────────────── 分区标题 ────────────────────────────────────────
class SectionLabel:
    def __init__(self, x, y, w, text, font, color=None):
        self.rect  = pygame.Rect(x, y, w, 20)
        self.text  = text
        self.font  = font
        self.color = color or COLORS["SidebarMuted"]

    def draw(self, surface):
        # 分割线
        mid_y = self.rect.y + 10
        pygame.draw.line(surface, COLORS["SidebarBorder"],
                         (self.rect.x, mid_y), (self.rect.right, mid_y))
        # 文字背景
        t = self.font.render(self.text, True, self.color)
        tw = t.get_width() + 12
        tx = self.rect.x + (self.rect.w - tw) // 2
        bg = pygame.Rect(tx, self.rect.y + 2, tw, 16)
        pygame.draw.rect(surface, COLORS["SidebarBg"], bg)
        surface.blit(t, (tx + 6, self.rect.y + 2))

# ─────────────────────────── 骰子面板 ────────────────────────────────────────
class DiceDisplay:
    """美化的骰子结果显示。"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 34

    def draw(self, surface, d1, d2, font):
        if d1 == 0:
            return
        total = d1 + d2
        is_double = (d1 == d2)

        for i, val in enumerate([d1, d2]):
            rx = self.x + i * (self.size + 8)
            ry = self.y
            rect = pygame.Rect(rx, ry, self.size, self.size)

            # 骰子主体
            pygame.draw.rect(surface, (245, 245, 250), rect, border_radius=7)
            if is_double:
                pygame.draw.rect(surface, COLORS["Gold"], rect, 2, border_radius=7)
            else:
                pygame.draw.rect(surface, (160, 165, 180), rect, 1, border_radius=7)

            # 骰子点
            _draw_dice_dots(surface, val, rect)

        # 总数标签
        total_str = f"= {total}" + (" 双骰!" if is_double else "")
        tc = COLORS["Gold"] if is_double else COLORS["SidebarText"]
        t = font.render(total_str, True, tc)
        surface.blit(t, (self.x + (self.size + 8) * 2 + 4, self.y + (self.size - t.get_height()) // 2))


def _draw_dice_dots(surface, value, rect):
    """在骰子矩形内绘制点数。"""
    cx, cy = rect.centerx, rect.centery
    r = rect.h // 10
    DOT_COLOR = (40, 40, 50)
    # (x偏移比例, y偏移比例) 相对于格子半径
    patterns = {
        1: [(0, 0)],
        2: [(-1, -1), (1, 1)],
        3: [(-1, -1), (0, 0), (1, 1)],
        4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
        5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)],
        6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)],
    }
    offset = rect.h // 4
    for dx, dy in patterns.get(value, []):
        pygame.draw.circle(surface, DOT_COLOR,
                           (cx + dx * offset, cy + dy * offset), r + 1)

# ─────────────────────────── 模态弹窗 ────────────────────────────────────────
class Modal:
    """带标题、正文和按钮的居中弹窗。"""
    def __init__(self, title, message, screen_w, screen_h, font_title, font_body,
                 btn1_text=None, btn1_cb=None, btn2_text=None, btn2_cb=None):
        w, h = 480, 230
        x = (screen_w - w) // 2
        y = (screen_h - h) // 2
        self.rect      = pygame.Rect(x, y, w, h)
        self.title     = title
        self.message   = message
        self.font_title = font_title
        self.font_body  = font_body
        self.visible    = True

        btn_y = y + h - 62
        self.buttons = []
        if btn1_text:
            b1 = Button(x + 24, btn_y, 200, 42, btn1_text, font_body,
                        COLORS["BtnBuy"], COLORS["BtnBuyHov"], btn1_cb, icon="buy")
            self.buttons.append(b1)
        if btn2_text:
            bx = x + w - 224 if btn1_text else x + (w - 200) // 2
            b2 = Button(bx, btn_y, 200, 42, btn2_text, font_body,
                        COLORS["BtnNeutral"], COLORS["BtnNeutralHov"], btn2_cb)
            self.buttons.append(b2)

    def draw(self, surface):
        if not self.visible:
            return
        # 半透明遮罩
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 155))
        surface.blit(overlay, (0, 0))

        # 卡片阴影
        sh = pygame.Surface((self.rect.w + 8, self.rect.h + 8), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 80), sh.get_rect(), border_radius=16)
        surface.blit(sh, (self.rect.x - 2, self.rect.y + 4))

        # 卡片主体
        pygame.draw.rect(surface, COLORS["SidebarPanel"], self.rect, border_radius=14)

        # 顶部彩色条
        top_bar = pygame.Rect(self.rect.x, self.rect.y, self.rect.w, 48)
        pygame.draw.rect(surface, COLORS["SidebarPanel2"], top_bar,
                         border_top_left_radius=14, border_top_right_radius=14)

        # 标题
        title_surf = self.font_title.render(self.title, True, COLORS["Gold"])
        surface.blit(title_surf, (self.rect.x + 20, self.rect.y + 12))

        # 外框
        pygame.draw.rect(surface, COLORS["SidebarAccent"], self.rect, 2, border_radius=14)

        # 正文（逐字符换行）
        y = self.rect.y + 60
        max_w = self.rect.width - 40
        current = ""
        lines = []
        for ch in self.message:
            if ch == "\n":
                lines.append(current); current = ""
            else:
                test = current + ch
                if self.font_body.size(test)[0] <= max_w:
                    current = test
                else:
                    lines.append(current); current = ch
        if current:
            lines.append(current)

        for ln in lines:
            txt = self.font_body.render(ln, True, COLORS["SidebarText"])
            surface.blit(txt, (self.rect.x + 20, y))
            y += self.font_body.get_height() + 4

        for btn in self.buttons:
            btn.draw(surface)

    def handle_event(self, event):
        if not self.visible:
            return
        for btn in self.buttons:
            btn.handle_event(event)
