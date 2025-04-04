import pygame
import random
import sys
import time
import math
from collections import Counter
from pygame.locals import *

# 初始化pygame
pygame.init()
pygame.font.init()

# 游戏常量
SCREEN_WIDTH = 1400  # 增加窗口宽度
SCREEN_HEIGHT = 900  # 增加窗口高度
BOARD_SIZE = 750    # 增加棋盘大小
MARGIN = 50
PLAYER_COLORS = [
    (231, 76, 60),    # 红
    (41, 128, 185),   # 蓝 
    (39, 174, 96),    # 绿
    (243, 156, 18),   # 黄
    (142, 68, 173),   # 紫
    (192, 57, 43),    # 深红
    (52, 152, 219),   # 浅蓝
    (241, 196, 15)    # 金色
]
PLAYER_AVATARS = [
    "♟",  # 红色玩家
    "♞",  # 蓝色玩家
    "♜",  # 绿色玩家
]
BACKGROUND_COLOR = (44, 62, 80)
BOARD_COLOR = (236, 240, 241)
CELL_COLOR = (255, 255, 255)
TEXT_COLOR = (44, 62, 80)
SPECIAL_CELL_COLORS = {
    "起点": (92, 230, 144),      # 浅绿色 (原46, 204, 113)
    "机会": (187, 143, 206),     # 浅紫色 (原155, 89, 182)
    "命运": (242, 171, 112),     # 浅橙色 (原230, 126, 34)
    "进监狱": (237, 132, 120),   # 浅红色 (原231, 76, 60)
    "监狱": (237, 132, 120),     # 浅红色 (原231, 76, 60)
    "所得税": (217, 120, 112),   # 浅红褐色 (原192, 57, 43)
    "奢侈税": (217, 120, 112),   # 浅红褐色 (原192, 57, 43)
    "公用事业": (133, 193, 233), # 浅蓝色 (原52, 152, 219)
    "铁路": (189, 195, 199),     # 浅灰色 (原149, 165, 166)
    "免费停车": (82, 209, 183)   # 浅青色 (原26, 188, 156)
}
PROPERTY_COLORS = [
    (129, 207, 224),  # Group 1
    (214, 162, 232),  # Group 2
    (255, 204, 153),  # Group 3
    (255, 153, 153),  # Group 4
    (255, 255, 153),  # Group 5
    (153, 255, 153),  # Group 6
    (153, 255, 255),  # Group 7
    (99, 125, 255)   # Group 8
]

# 创建游戏窗口
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("豪华大富翁 - 40格完整版")

# 加载骰子图片
def load_dice_images():
    dice_images = []
    for i in range(1, 7):
        try:
            img = pygame.image.load(f"dice_{i}.png")
            img = pygame.transform.scale(img, (60, 60))
            dice_images.append(img)
        except:
            # 如果图片不存在，创建简单的骰子图形
            img = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.rect(img, (255, 255, 255), (0, 0, 60, 60), 0, 10)
            dots = {
                1: [(30, 30)],
                2: [(20, 20), (40, 40)],
                3: [(20, 20), (30, 30), (40, 40)],
                4: [(20, 20), (20, 40), (40, 20), (40, 40)],
                5: [(20, 20), (20, 40), (30, 30), (40, 20), (40, 40)],
                6: [(20, 20), (20, 40), (30, 20), (30, 40), (40, 20), (40, 40)]
            }
            for dot in dots[i]:
                pygame.draw.circle(img, (0, 0, 0), dot, 5)
            dice_images.append(img)
    return dice_images

dice_images = load_dice_images()

# 字体
font_small = pygame.font.SysFont('simhei', 16)
font_medium = pygame.font.SysFont('simhei', 20)
font_large = pygame.font.SysFont('simhei', 28)
font_title = pygame.font.SysFont('simhei', 42, bold=True)

# 游戏状态
class GameState:
    def __init__(self):
        self.players = []
        self.properties = []
        self.current_player = None
        self.game_over = False
        self.dice_values = [1, 1]
        self.message = "游戏开始!"
        self.rolling_dice = False
        self.roll_start_time = 0
        self.roll_duration = 800  # 骰子动画持续时间(毫秒)
        self.double_count = 0  # 连续双骰次数
        self.has_rolled_dice = False  # 是否已经掷过骰子
        self.auction_property = None  # 正在拍卖的地产
        self.auction_bid = 0
        self.auction_player = 0
        self.chance_cards = []
        self.fate_cards = []
        self.showing_purchase_choice = False
        self.purchase_property = None
        self.selling_property = None
        self.selling_price = 0
        self.selling_to = None
        self.mortgage_mode = False
        self.unmortgage_mode = False
        self.selling_houses = False
        self.current_debt = 0
        self.creditor = None
        self.rent_message = ""
        self.show_rent_message = False
        self.show_card_message = False
        self.card_message = ""
        self.card_type = ""
        self.auction_confirmed_players = set()
        self.auction_highest_bidder = None
        self.auction_passed_players = set()
        self.auction_bids = {}
        self.auction_status = {}
        self.init_cards()
        
    def init_cards(self):
        # 初始化机会卡
        self.chance_cards = [
            "前进到起点",
            "前进到铁路1",
            "前进到铁路2",
            "前进到公用事业",
            "后退3步",
            "获得建筑补贴: 每栋房屋$25, 每家酒店$100",
            "获得股息$50",
            "出狱卡(可保留)",
            "直接前往监狱",
            "道路维修费: 每栋房屋$40, 每家酒店$115",
            "银行错误对你有利, 获得$200",
            "缴纳罚款$15",
            "前往最近的铁路(经过起点可获得$200)",
            "前往最近的公用事业",
            "选举捐款每人$20",
            "你的建筑贷款到期, 获得$150"
        ]
        random.shuffle(self.chance_cards)
        
        # 初始化命运卡
        self.fate_cards = [
            "前进到起点",
            "获得遗产$100",
            "缴纳学校税$150",
            "股票销售获利$50",
            "出狱卡(可保留)",
            "直接前往监狱",
            "美丽城市竞赛第二名, 获得$10",
            "生日礼物, 每位玩家给你$10",
            "医生费用$50",
            "出售股票获利$50",
            "医院费用$100",
            "保险到期$100",
            "缴纳所得税$20",
            "获得咨询费$25",
            "街道维修费: 每栋房屋$40, 每家酒店$115",
            "假期基金分红$100"
        ]
        random.shuffle(self.fate_cards)
        
    def add_player(self, name):
        self.players.append({
            "name": name,
            "position": 0,  # 确保从起点开始
            "money": 1500,
            "properties": [],
            "in_jail": False,
            "jail_turns": 0,
            "ai": False,
            "get_out_of_jail_cards": 0,
            "bankrupt": False
        })
    
    def add_ai_player(self, name):
        self.players.append({
            "name": name,
            "position": 0,  # 确保从起点开始
            "money": 1500,
            "properties": [],
            "in_jail": False,
            "jail_turns": 0,
            "ai": True,
            "get_out_of_jail_cards": 0,
            "bankrupt": False
        })
    
    def init_properties(self):
        # 40个格子的完整大富翁布局
        property_names = [
            "起点", "北京路", "命运", "上海街", "所得税", 
            "铁路1", "广州大道", "机会", "深圳中心", "成都广场", 
            "监狱", "杭州花园", "公用事业1", "重庆大厦", "武汉广场", 
            "铁路2", "西安古城", "命运", "苏州园林", "南京路", 
            "免费停车", "天津街", "机会", "长沙中心", "厦门湾", 
            "铁路3", "青岛海滨", "大连广场", "公用事业2", "哈尔滨中心", 
            "进监狱", "长春广场", "沈阳中心", "命运", "济南广场", 
            "铁路4", "机会", "石家庄中心", "奢侈税", "郑州中心"
        ]
        
        property_prices = [
            0,   60,   0,   60,   0,    # 1-5
            200, 100,   0, 100, 120,    # 6-10
            0,  140, 150, 140, 160,     # 11-15
            200, 180,   0, 180, 200,     # 16-20
            0,  220,   0, 220, 240,      # 21-25
            200, 260, 260, 150, 280,     # 26-30
            0,  300, 300,   0, 320,      # 31-35
            200,   0, 350,   0, 400      # 36-40
        ]
        
        property_rents = [
            0,    2,   0,    4,   0,    # 1-5
            25,    6,   0,    6,    8,   # 6-10
            0,   10,    0,   10,   12,   # 11-15
            25,   14,   0,   14,   16,   # 16-20
            0,   18,   0,   18,   20,    # 21-25
            25,   22,   22,    0,   24,  # 26-30
            0,   26,   26,   0,   28,    # 31-35
            25,   0,   35,   0,   50     # 36-40
        ]
        
        property_groups = [
            -1,  0, -1,  0, -1,   # 1-5 (起点、命运、所得税)
            -2,  1, -1,  1,  1,    # 6-10 (铁路、机会)
            -1,  2, -3,  2,  2,    # 11-15 (监狱、公用事业)
            -2,  3, -1,  3,  3,    # 16-20 (铁路、命运)
            -1,  4, -1,  4,  4,    # 21-25 (免费停车、机会)
            -2,  5,  5, -3,  5,    # 26-30 (铁路、公用事业)
            -1,  6,  6, -1,  6,    # 31-35 (进监狱、命运)
            -2, -1,  7, -1,  7     # 36-40 (铁路、机会、奢侈税)
        ]
        
        # -1: 特殊格子(机会/命运等)
        # -2: 铁路
        # -3: 公用事业
        # 0-7: 地产颜色组
        
        for i in range(40):
            self.properties.append({
                "name": property_names[i],
                "price": property_prices[i],
                "owner": None,
                "rent": property_rents[i],
                "houses": 0,
                "hotel": False,
                "group": property_groups[i],
                "mortgaged": False
            })
    
    def draw_chance_card(self):
        if not self.chance_cards:
            self.init_cards()  # 如果牌堆空了就重新洗牌
        card = self.chance_cards.pop()
        return card
    
    def draw_fate_card(self):
        if not self.fate_cards:
            self.init_cards()  # 如果牌堆空了就重新洗牌
        card = self.fate_cards.pop()
        return card

# 初始化游戏
game = GameState()
game.init_properties()

# 添加玩家
game.add_player("玩家1")
game.add_player("玩家2")
game.add_player("玩家3")  # 新增第三个玩家

# 随机选择一个玩家开始
game.current_player = random.randint(0, len(game.players) - 1)
game.message = f"{game.players[game.current_player]['name']}的回合, 点击掷骰子键继续"

# 游戏主循环
def main():
    clock = pygame.time.Clock()
    
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == MOUSEBUTTONDOWN and event.button == 1:  # 左键点击
                mouse_pos = pygame.mouse.get_pos()
                # 检查是否点击了骰子按钮
                if hasattr(game, 'dice_button_rect') and game.dice_button_rect.collidepoint(mouse_pos):
                    if hasattr(game, 'can_roll_dice') and game.can_roll_dice:
                        start_dice_roll()
                # 检查是否点击了结束回合按钮
                elif hasattr(game, 'end_turn_button_rect') and game.end_turn_button_rect.collidepoint(mouse_pos):
                    if hasattr(game, 'can_end_turn') and game.can_end_turn:
                        end_turn()
                # 检查是否点击了拍卖确认按钮
                elif hasattr(game, 'confirm_button_rect') and game.confirm_button_rect.collidepoint(mouse_pos):
                    if game.auction_property is not None:
                        handle_auction_confirmation(game.auction_player)
                # 检查是否点击了拍卖放弃按钮
                elif hasattr(game, 'pass_button_rect') and game.pass_button_rect.collidepoint(mouse_pos):
                    if game.auction_property is not None:
                        handle_auction_pass(game.auction_player)
            
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    if game.auction_property is not None:
                        # 当前玩家放弃竞价
                        handle_auction_pass(game.auction_player)
                    elif game.selling_property is not None:
                        game.selling_property = None
                        game.mortgage_mode = False
                        game.unmortgage_mode = False
                        game.selling_houses = False
                    else:
                        pygame.quit()
                        sys.exit()
                
                # 处理租金消息
                if game.show_rent_message and event.key == K_SPACE:
                    game.show_rent_message = False
                    continue
                
                # 处理卡片消息
                if game.show_card_message and event.key == K_SPACE:
                    game.show_card_message = False
                    continue
                
                # 处理拍卖
                if game.auction_property is not None:
                    if event.key == K_UP:
                        # 增加出价
                        current_bid = game.auction_bids[game.auction_player]
                        if current_bid + 10 <= game.players[game.auction_player]["money"]:
                            game.auction_bids[game.auction_player] = current_bid + 10
                            update_auction_message()
                    elif event.key == K_DOWN:
                        # 减少出价，但不能低于最低出价
                        current_bid = game.auction_bids[game.auction_player]
                        min_bid = max(10, game.auction_highest_bid + 10 if game.auction_highest_bid else 10)
                        if current_bid - 10 >= min_bid:
                            game.auction_bids[game.auction_player] = current_bid - 10
                            update_auction_message()
                    elif event.key == K_RETURN:
                        handle_auction_confirmation(game.auction_player)
                    continue
                
                if hasattr(game, 'rent_message') and game.rent_message:
                    if event.key == K_SPACE:
                        game.rent_message = None
                    continue
                
                if game.showing_purchase_choice:
                    if event.key in [K_y, K_RETURN]:
                        handle_purchase_choice("Y")
                    elif event.key in [K_n, K_SPACE]:
                        handle_purchase_choice("N")
                
                # 处理资金不足时的选项
                if game.current_debt > 0:
                    if event.key == K_1:
                        start_property_sale(game.players[game.current_player])
                    elif event.key == K_2:
                        start_mortgage(game.players[game.current_player])
                    elif event.key == K_3:
                        start_selling_houses(game.players[game.current_player])
                    elif event.key == K_4:
                        handle_bankruptcy(game.players[game.current_player], game.creditor)
                        game.current_debt = 0
                        game.creditor = None
                
                # 处理地产出售
                elif game.selling_property is not None:
                    if game.mortgage_mode:
                        handle_mortgage(event.key)
                    elif game.unmortgage_mode:
                        handle_unmortgage(event.key)
                    elif game.selling_houses:
                        handle_house_sale(event.key)
                    else:
                        handle_property_sale(event.key)
        
        # AI自动行动
        if not game.game_over and not game.rolling_dice and game.auction_property is None:
            current_player = game.players[game.current_player]
            if current_player["ai"] and not current_player["bankrupt"]:
                pygame.time.delay(800)
                start_dice_roll()
        
        # 更新骰子动画
        if game.rolling_dice:
            update_dice_roll()
        
        draw_game()
        pygame.display.update()
        clock.tick(30)

# 开始骰子动画
def start_dice_roll():
    if game.players[game.current_player]["in_jail"]:
        handle_in_jail()
        return
    
    game.rolling_dice = True
    game.roll_start_time = pygame.time.get_ticks()
    game.dice_values = [random.randint(1, 6), random.randint(1, 6)]
    game.has_rolled_dice = True

# 更新骰子动画
def update_dice_roll():
    current_time = pygame.time.get_ticks()
    if current_time - game.roll_start_time >= game.roll_duration:
        game.rolling_dice = False
        handle_dice_result()
    else:
        # 动画期间随机切换骰子值
        if random.random() < 0.2:
            game.dice_values = [random.randint(1, 6), random.randint(1, 6)]

# 处理骰子结果
def handle_dice_result():
    player = game.players[game.current_player]
    total = sum(game.dice_values)
    
    # 检查是否双骰
    if game.dice_values[0] == game.dice_values[1]:
        game.double_count += 1
        game.message = f"{player['name']}掷出了双骰 {game.dice_values[0]}+{game.dice_values[1]} (连续{game.double_count}次)"
        
        if game.double_count >= 3:
            game.message += ", 连续三次双骰被送进监狱!"
            send_to_jail(player)
            end_turn()
            return
    else:
        game.double_count = 0
    
    # 移动玩家
    new_position = (player["position"] + total) % 40
    player["position"] = new_position
    
    # 处理当前格子
    handle_landing(player)
    
    # 如果是双骰且玩家未进监狱，可以再掷一次
    if game.dice_values[0] == game.dice_values[1] and not player["in_jail"]:
        game.message += ", 可以再掷一次!"
    else:
        game.message += "\n可以结束回合"

# 处理玩家落在格子上
def handle_landing(player):
    current_pos = player["position"]
    prop = game.properties[current_pos]
    total = sum(game.dice_values)
    
    game.message = f"{player['name']}掷出了{game.dice_values[0]}+{game.dice_values[1]}={total}, 到达了{prop['name']}"
    
    # 特殊格子处理
    if prop["name"] == "起点":
        player["money"] += 200
        game.message += ", 获得200元"
    elif prop["name"] in ["机会", "命运"]:
        if prop["name"] == "机会":
            card = game.draw_chance_card()
            game.card_type = "机会"
        else:
            card = game.draw_fate_card()
            game.card_type = "命运"
        
        game.card_message = card
        game.show_card_message = True
        handle_card(player, card, prop["name"])
    elif prop["name"] == "所得税":
        tax = min(200, player["money"] // 10)
        player["money"] -= tax
        game.message += f", 缴纳所得税{tax}元"
        game.rent_message = f"{player['name']}需要缴纳所得税{tax}元"
        game.show_rent_message = True
    elif prop["name"] == "奢侈税":
        tax = min(100, player["money"] // 5)
        player["money"] -= tax
        game.message += f", 缴纳奢侈税{tax}元"
        game.rent_message = f"{player['name']}需要缴纳奢侈税{tax}元"
        game.show_rent_message = True
    elif prop["name"] == "进监狱":
        send_to_jail(player)
    elif prop["name"] == "监狱":
        game.message += ", 只是探监"
    elif prop["name"] == "免费停车":
        game.message += ", 休息一回合"
    elif prop["group"] == -2:  # 铁路
        handle_railroad(player, prop)
    elif prop["group"] == -3:  # 公用事业
        handle_utility(player, prop)
    elif prop["owner"] is None and prop["price"] > 0:  # 无主地产
        handle_unowned_property(player, prop)
    elif prop["owner"] == game.current_player:  # 自己的地产
        game.message += ", 自己的地产"
    else:  # 他人地产
        handle_owned_property(player, prop)

# 处理机会/命运卡
def handle_card(player, card, card_type):
    try:
        # 移动类卡片
        if "前进到起点" in card:
            player["position"] = 0
            player["money"] += 200
            game.message += ", 获得200元"
            handle_landing(player)  # 确保处理落地效果
        elif "前进到铁路" in card or "前往最近的铁路" in card:
            # 找到最近的铁路
            railroads = [i for i, p in enumerate(game.properties) if p["group"] == -2]
            current_pos = player["position"]
            next_railroad = min(railroads, key=lambda x: (x - current_pos) % 40)
            player["position"] = next_railroad  # 直接更新位置
            game.message += f", 移动到了{game.properties[next_railroad]['name']}"
            if current_pos > next_railroad:  # 经过了起点
                player["money"] += 200
                game.message += " 并经过起点获得200元"
            handle_landing(player)  # 处理落地效果
        elif "前进到公用事业" in card or "前往最近的公用事业" in card:
            # 找到最近的公用事业
            utilities = [i for i, p in enumerate(game.properties) if p["group"] == -3]
            current_pos = player["position"]
            next_utility = min(utilities, key=lambda x: (x - current_pos) % 40)
            player["position"] = next_utility  # 更新玩家位置
            prop = game.properties[next_utility]
            game.message += f", 移动到了{prop['name']}"
            if current_pos > next_utility:  # 经过了起点
                player["money"] += 200
                game.message += " 并经过起点获得200元"
            handle_landing(player)  # 处理落地效果
        elif "后退" in card:
            try:
                steps = int(''.join(filter(str.isdigit, card)))
                current_pos = player["position"]
                new_pos = (current_pos - steps) % 40
                player["position"] = new_pos
                game.message += f", 后退{steps}步到{game.properties[new_pos]['name']}"
                handle_landing(player)  # 处理落地效果
            except ValueError:
                game.message += ", 无法解析步数"
        elif "直接前往监狱" in card:
            send_to_jail(player)
        elif "前进" in card:  # 处理其他前进类卡片
            try:
                steps = int(''.join(filter(str.isdigit, card)))
                current_pos = player["position"]
                new_pos = (current_pos + steps) % 40
                player["position"] = new_pos
                game.message += f", 前进{steps}步到{game.properties[new_pos]['name']}"
                # 检查是否经过起点
                if new_pos < current_pos:
                    player["money"] += 200
                    game.message += " 并经过起点获得200元"
                handle_landing(player)  # 处理落地效果
            except ValueError:
                game.message += ", 无法解析步数"
        
        # 金钱类卡片
        elif any(keyword in card for keyword in ["获得", "缴纳", "支付"]):
            try:
                # 提取数字
                amount = int(''.join(filter(str.isdigit, card)))
                if "获得" in card:
                    player["money"] += amount
                    game.message += f", 获得{amount}元"
                else:
                    player["money"] -= amount
                    game.message += f", 支付{amount}元"
            except ValueError:
                game.message += ", 无法解析金额"
        
        # 特殊卡片
        elif "出狱卡" in card:
            player["get_out_of_jail_cards"] += 1
            game.message += ", 获得出狱卡"
        
        # 与其他玩家互动的卡片
        elif "每位玩家给你" in card or "向每位玩家收取" in card:
            try:
                amount = int(''.join(filter(str.isdigit, card)))
                total = 0
                for p in game.players:
                    if p != player and not p["bankrupt"]:
                        payment = min(amount, p["money"])
                        p["money"] -= payment
                        total += payment
                player["money"] += total
                game.message += f", 从其他玩家处获得共{total}元"
            except ValueError:
                game.message += ", 无法解析金额"
        
        # 建筑相关卡片
        elif "建筑补贴" in card:
            # 计算玩家拥有的地产数量
            property_count = len(player["properties"])
            subsidy = property_count * 25
            player["money"] += subsidy
            game.message += f", 获得建筑补贴{subsidy}元(每块地产25元)"
        elif "道路维修费" in card or "街道维修费" in card:
            # 计算玩家拥有的地产数量
            property_count = len(player["properties"])
            maintenance_fee = property_count * 40
            player["money"] -= maintenance_fee
            game.message += f", 支付维修费{maintenance_fee}元(每块地产40元)"
        
        else:
            game.message += f", 未知卡片效果: {card}"
    
    except Exception as e:
        game.message += f", 处理卡片时出错: {str(e)}"

# 处理铁路
def handle_railroad(player, prop):
    if prop["owner"] is None:
        handle_unowned_property(player, prop)
    elif prop["owner"] == game.current_player:
        game.message += ", 自己的铁路"
    else:
        owner = game.players[prop["owner"]]
        # 计算拥有的铁路数量
        railroads = [p for p in game.properties if p["group"] == -2 and p["owner"] == prop["owner"]]
        rent = 25 * (2 ** (len(railroads) - 1))  # 1条25, 2条50, 3条100, 4条200
        pay_rent(player, owner, rent, "铁路租金")

# 处理公用事业
def handle_utility(player, prop):
    if prop["owner"] is None:
        handle_unowned_property(player, prop)
    elif prop["owner"] == game.current_player:
        game.message += ", 自己的公用事业"
    else:
        owner = game.players[prop["owner"]]
        # 计算拥有的公用事业数量
        utilities = [p for p in game.properties if p["group"] == -3 and p["owner"] == prop["owner"]]
        dice_total = sum(game.dice_values)
        if len(utilities) == 1:
            rent = dice_total * 4
        else:
            rent = dice_total * 10
        pay_rent(player, owner, rent, "公用事业租金")

# 处理无主地产
def handle_unowned_property(player, prop):
    if player["ai"]:
        # AI购买逻辑保持不变
        if random.random() > 0.3:  # 70%几率购买
            buy_property(player, prop)
        else:
            start_auction(prop)
    else:
        # 显示购买选择界面
        game.showing_purchase_choice = True
        game.purchase_property = prop
        game.message = f"是否购买 {prop['name']}? 价格: ${prop['price']} (Y键购买, N键拍卖)"

# 开始拍卖
def start_auction(prop):
    """开始拍卖"""
    game.auction_property = prop
    game.auction_player = game.current_player  # 从当前玩家开始
    
    # 初始化拍卖状态
    game.auction_bids = {}
    game.auction_status = {}
    game.auction_highest_bid = 0
    game.auction_highest_bidder = None
    
    # 设置所有未破产玩家的状态为pending
    for i, player in enumerate(game.players):
        if not player["bankrupt"]:
            game.auction_status[i] = "pending"
            game.auction_bids[i] = 0
    
    # 设置当前玩家的建议出价为地产原价的一半
    game.auction_bids[game.auction_player] = prop["price"] // 2
    
    update_auction_message()

def handle_auction_confirmation(player_idx):
    """处理拍卖确认"""
    current_bid = game.auction_bids[player_idx]
    player = game.players[player_idx]
    
    # 检查出价是否有效
    if current_bid < 10:
        game.message = f"出价不能低于10元"
        return
    
    if current_bid > player["money"]:
        game.message = f"资金不足"
        return
    
    # 更新玩家状态为bidding
    game.auction_status[player_idx] = "bidding"
    
    # 更新最高价和最高价玩家
    game.auction_highest_bid = current_bid
    game.auction_highest_bidder = player_idx
    
    # 检查是否需要结束拍卖
    if check_auction_end():
        end_auction()
        return
    
    # 找到下一个可以竞价的玩家
    next_player = find_next_player_to_bid()
    if next_player is not None:
        game.auction_player = next_player
        # 设置下一个玩家的建议出价为当前最高价+10
        game.auction_bids[next_player] = game.auction_highest_bid + 10
        update_auction_message()
    else:
        end_auction()

def handle_auction_pass(player_idx):
    """处理玩家放弃竞价"""
    game.auction_status[player_idx] = "withdrawed"
    game.auction_bids[player_idx] = 0
    
    # 检查是否需要结束拍卖
    if check_auction_end():
        end_auction()
        return
    
    # 找到下一个可以竞价的玩家
    next_player = find_next_player_to_bid()
    if next_player is not None:
        game.auction_player = next_player
        # 如果有人出过价，设置建议出价为最高价+10，否则为10
        if game.auction_highest_bid > 0:
            game.auction_bids[next_player] = game.auction_highest_bid + 10
        else:
            game.auction_bids[next_player] = 10
        update_auction_message()
    else:
        end_auction()

def check_auction_end():
    """检查是否需要结束拍卖"""
    auction_status_count = Counter(game.auction_status.values())
    if auction_status_count["pending"] == 0 and auction_status_count["bidding"] == 1:
        return True
    return False

def end_auction():
    """结束拍卖"""
    prop = game.auction_property
    
    # 计算pending和bidding的玩家
    pending_count = 0
    bidding_count = 0
    last_pending = None
    last_bidding = None
    
    for player_idx, status in game.auction_status.items():
        if status == "pending":
            pending_count += 1
            last_pending = player_idx
        elif status == "bidding":
            bidding_count += 1
            last_bidding = player_idx
    
    winner = None
    final_price = 0
    
    if bidding_count == 1 and pending_count == 0:
        # 只有一个bidding玩家，以最高价成交
        winner = last_bidding
        final_price = game.auction_highest_bid
    elif pending_count == 1 and bidding_count == 0:
        # 只有一个pending玩家，以底价成交
        winner = last_pending
        final_price = 10
        # 检查玩家是否有足够的钱支付底价
        if game.players[winner]["money"] < final_price:
            game.message = f"拍卖流拍，{game.players[winner]['name']}资金不足支付底价"
            game.auction_property = None
            return
    
    if winner is not None:
        # 执行购买
        winner_player = game.players[winner]
        winner_player["money"] -= final_price
        winner_player["properties"].append(game.properties.index(prop))
        prop["owner"] = winner
        
        game.message = f"{winner_player['name']}以${final_price}购得{prop['name']}"
    else:
        game.message = f"{prop['name']}拍卖流拍"
    
    # 清理拍卖状态
    game.auction_property = None
    game.auction_bids = {}
    game.auction_status = {}
    game.auction_highest_bidder = None

def update_auction_message():
    """更新拍卖信息显示"""
    prop = game.auction_property
    player = game.players[game.auction_player]
    current_bid = game.auction_bids[game.auction_player]
    
    # 计算各种状态的玩家数量
    pending_count = sum(1 for status in game.auction_status.values() if status == "pending")
    bidding_count = sum(1 for status in game.auction_status.values() if status == "bidding")
    withdrawed_count = sum(1 for status in game.auction_status.values() if status == "withdrawed")
    
    # 构建拍卖信息
    message = f"{prop['name']}拍卖中"
    if game.auction_highest_bidder is not None:
        highest_bidder = game.players[game.auction_highest_bidder]
        message += f"\n当前最高价: ${game.auction_highest_bid} (出价者: {highest_bidder['name']})"
    else:
        message += f"\n当前最高价: $0"
    
    message += f"\n当前竞拍者: {player['name']}"
    message += f"\n您的出价: ${current_bid}"
    message += f"\n最低可出价: ${max(10, game.auction_highest_bid + 10)}"
    message += f"\n最高可出价: ${player['money']}"
    message += f"\n待定玩家: {pending_count}人"
    message += f"\n已出价玩家: {bidding_count}人"
    message += f"\n已放弃玩家: {withdrawed_count}人"
    message += "\n上下键调整出价，回车确认，ESC放弃"
    
    game.message = message

# 购买地产
def buy_property(player, prop):
    player["money"] -= prop["price"]
    player["properties"].append(game.properties.index(prop))
    prop["owner"] = game.current_player
    game.message += f", 购买了{prop['name']}"

# 支付租金
def pay_rent(player, owner, amount, reason):
    if player["money"] >= amount:
        player["money"] -= amount
        owner["money"] += amount
        game.rent_message = f"{player['name']}需要支付{amount}元{reason}给{owner['name']}"
        game.show_rent_message = True  # 新增标志
    else:
        game.message = f"{player['name']}需要支付{amount}元{reason}给{owner['name']}"
        if not handle_insufficient_funds(player, amount, owner):
            handle_bankruptcy(player, owner)

# 处理破产
def handle_bankruptcy(player, creditor):
    # 转移所有资产
    for prop_idx in player["properties"]:
        prop = game.properties[prop_idx]
        if creditor:  # 如果有债权人，资产转给债权人
            prop["owner"] = game.players.index(creditor)
            creditor["properties"].append(prop_idx)
        else:  # 如果没有债权人（比如税收导致破产），资产重新可供购买
            prop["owner"] = None
            prop["houses"] = 0
            prop["hotel"] = False
    
    player["properties"] = []
    player["money"] = 0
    player["bankrupt"] = True
    
    # 检查游戏是否结束
    active_players = sum(1 for p in game.players if not p["bankrupt"])
    if active_players <= 1:
        game.game_over = True
        for p in game.players:
            if not p["bankrupt"]:
                game.message = f"游戏结束! {p['name']}获胜!"
                break

# 送玩家进监狱
def send_to_jail(player):
    player["position"] = 10  # 监狱位置
    player["in_jail"] = True
    player["jail_turns"] = 0
    game.double_count = 0
    game.message += ", 被送进监狱!"

# 处理监狱中的玩家
def handle_in_jail():
    player = game.players[game.current_player]
    player["jail_turns"] += 1
    
    if player["get_out_of_jail_cards"] > 0:
        # 使用出狱卡
        player["get_out_of_jail_cards"] -= 1
        player["in_jail"] = False
        player["jail_turns"] = 0
        game.message = f"{player['name']}使用出狱卡离开监狱"
        start_dice_roll()
    elif player["money"] >= 50:
        # 支付保释金
        player["money"] -= 50
        player["in_jail"] = False
        player["jail_turns"] = 0
        game.message = f"{player['name']}支付50元保释金离开监狱"
        start_dice_roll()
    elif game.dice_values[0] == game.dice_values[1]:
        # 掷出双骰
        player["in_jail"] = False
        player["jail_turns"] = 0
        game.message = f"{player['name']}掷出双骰离开监狱"
        handle_dice_result()
    else:
        if player["jail_turns"] >= 3:
            # 第三次必须支付50元
            if player["money"] >= 50:
                player["money"] -= 50
                player["in_jail"] = False
                player["jail_turns"] = 0
                game.message = f"{player['name']}第三次必须支付50元离开监狱"
                start_dice_roll()
            else:
                game.message = f"{player['name']}无法支付50元保释金! 破产!"
                handle_bankruptcy(player, None)
        else:
            game.message = f"{player['name']}仍在监狱中(第{player['jail_turns']}回合)"
            end_turn()

# 结束当前回合
def end_turn():
    # 检查游戏是否结束
    active_players = [p for p in game.players if not p["bankrupt"]]
    if len(active_players) <= 1:
        game.game_over = True
        return
    
    # 找到下一个未破产的玩家
    next_player = (game.current_player + 1) % len(game.players)
    while game.players[next_player]["bankrupt"]:
        next_player = (next_player + 1) % len(game.players)
    
    game.current_player = next_player
    game.has_rolled_dice = False
    game.double_count = 0
    
    # 更新消息
    current_player = game.players[game.current_player]
    if current_player["ai"]:
        game.message = f"{current_player['name']}的回合(电脑)"
    else:
        game.message = f"{current_player['name']}的回合"

# 绘制游戏界面
def draw_game():
    # 背景
    screen.fill(BACKGROUND_COLOR)
    
    # 绘制标题
    title_surface = font_title.render("豪华大富翁 - 40格完整版", True, (255, 255, 255))
    screen.blit(title_surface, (SCREEN_WIDTH // 2 - title_surface.get_width() // 2, 10))
    
    # 绘制游戏板
    draw_board()
    
    # 绘制玩家信息
    draw_player_info()
    
    # 绘制当前消息（移到右下角）
    msg_width = SCREEN_WIDTH - (MARGIN * 2 + BOARD_SIZE) - MARGIN * 2
    msg_height = 150  # 进一步增加消息框高度
    msg_x = MARGIN * 2 + BOARD_SIZE
    msg_y = SCREEN_HEIGHT - MARGIN - msg_height
    
    msg_bg = pygame.Rect(msg_x, msg_y, msg_width, msg_height)
    pygame.draw.rect(screen, (52, 73, 94), msg_bg, 0, 10)
    pygame.draw.rect(screen, (149, 165, 166), msg_bg, 2, 10)
    
    # 调整文字大小和行距
    msg_lines = wrap_text(game.message, font_medium, msg_width - 40)  # 减小文本宽度，增加边距
    line_height = 30  # 增加行距
    max_lines = (msg_height - 20) // line_height  # 计算最大可显示行数
    
    # 如果行数超过最大显示行数，只显示最后几行
    if len(msg_lines) > max_lines:
        msg_lines = msg_lines[-max_lines:]
    
    for i, line in enumerate(msg_lines):
        msg_surface = font_medium.render(line, True, (255, 255, 255))
        screen.blit(msg_surface, (msg_x + 20, msg_y + 10 + i * line_height))
    
    # 绘制租金消息
    if game.show_rent_message:
        draw_rent_message()
    
    # 绘制拍卖界面
    if game.auction_property is not None:
        draw_auction()
    
    # 绘制购买选择界面
    if game.showing_purchase_choice:
        draw_purchase_choice()
    
    # 绘制当前债务信息
    if game.current_debt > 0:
        draw_debt_info()
    
    # 绘制地产出售界面
    if game.selling_property is not None:
        if game.mortgage_mode:
            draw_mortgage_ui()
        elif game.unmortgage_mode:
            draw_unmortgage_ui()
        elif game.selling_houses:
            draw_house_sale_ui()
        else:
            draw_property_sale_ui()
    
    # 游戏结束显示
    if game.game_over:
        draw_game_over()
    
    # 绘制卡片消息
    if game.show_card_message:
        draw_card_message()

# 绘制拍卖界面
def draw_auction():
    """绘制拍卖界面"""
    prop = game.auction_property
    auction_bg = pygame.Rect(SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 - 200, 600, 400)
    pygame.draw.rect(screen, (44, 62, 80), auction_bg, 0, 15)
    pygame.draw.rect(screen, (52, 152, 219), auction_bg, 3, 15)
    
    title = font_large.render("拍卖", True, (255, 255, 255))
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 160))
    
    prop_name = font_large.render(prop["name"], True, (255, 255, 255))
    screen.blit(prop_name, (SCREEN_WIDTH // 2 - prop_name.get_width() // 2, SCREEN_HEIGHT // 2 - 120))
    
    # 显示当前出价
    current_bid = game.auction_bids[game.auction_player]
    bid_text = font_large.render(f"当前出价: ${current_bid}", True, (255, 255, 255))
    screen.blit(bid_text, (SCREEN_WIDTH // 2 - bid_text.get_width() // 2, SCREEN_HEIGHT // 2 - 60))
    
    # 显示最高出价
    if game.auction_highest_bidder is not None:
        highest_bid = game.auction_bids[game.auction_highest_bidder]
        highest_bidder = game.players[game.auction_highest_bidder]["name"]
        highest_bid_text = font_large.render(f"最高出价: ${highest_bid} ({highest_bidder})", True, (255, 255, 255))
        screen.blit(highest_bid_text, (SCREEN_WIDTH // 2 - highest_bid_text.get_width() // 2, SCREEN_HEIGHT // 2))
    
    current_player = game.players[game.auction_player]
    player_text = font_large.render(f"当前竞拍者: {current_player['name']}", True, PLAYER_COLORS[game.auction_player])
    screen.blit(player_text, (SCREEN_WIDTH // 2 - player_text.get_width() // 2, SCREEN_HEIGHT // 2 + 60))
    
    # 绘制确认按钮
    confirm_button = pygame.Rect(SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 + 120, 150, 50)
    pygame.draw.rect(screen, (46, 204, 113), confirm_button, 0, 10)
    pygame.draw.rect(screen, (39, 174, 96), confirm_button, 2, 10)
    confirm_text = font_large.render("确认", True, (255, 255, 255))
    screen.blit(confirm_text, (confirm_button.x + confirm_button.width//2 - confirm_text.get_width()//2, 
                              confirm_button.y + confirm_button.height//2 - confirm_text.get_height()//2))
    
    # 绘制放弃按钮
    pass_button = pygame.Rect(SCREEN_WIDTH // 2 + 30, SCREEN_HEIGHT // 2 + 120, 150, 50)
    pygame.draw.rect(screen, (231, 76, 60), pass_button, 0, 10)
    pygame.draw.rect(screen, (192, 57, 43), pass_button, 2, 10)
    pass_text = font_large.render("放弃", True, (255, 255, 255))
    screen.blit(pass_text, (pass_button.x + pass_button.width//2 - pass_text.get_width()//2, 
                           pass_button.y + pass_button.height//2 - pass_text.get_height()//2))
    
    # 保存按钮位置供点击检测使用
    game.confirm_button_rect = confirm_button
    game.pass_button_rect = pass_button
    
    # 显示调整出价提示
    hint = font_medium.render("上下键调整价格", True, (200, 200, 200))
    screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT // 2 + 180))

# 绘制游戏结束界面
def draw_game_over():
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    winner = None
    for player in game.players:
        if not player["bankrupt"]:
            winner = player
            break
    
    if winner:
        end_msg = f"游戏结束! {winner['name']}获胜!"
    else:
        end_msg = "游戏结束! 平局!"
    
    end_bg = pygame.Rect(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 100, 500, 200)
    pygame.draw.rect(screen, (44, 62, 80), end_bg, 0, 20)
    pygame.draw.rect(screen, (52, 152, 219), end_bg, 3, 20)
    
    end_surface = font_large.render(end_msg, True, (255, 255, 255))
    screen.blit(end_surface, (SCREEN_WIDTH // 2 - end_surface.get_width() // 2, 
                               SCREEN_HEIGHT // 2 - 50))
    
    restart_surface = font_medium.render("按ESC键退出游戏", True, (200, 200, 200))
    screen.blit(restart_surface, (SCREEN_WIDTH // 2 - restart_surface.get_width() // 2, 
                                 SCREEN_HEIGHT // 2 + 20))

# 文本换行函数
def wrap_text(text, font, max_width):
    words = text.split(' ')
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        if font.size(test_line)[0] <= max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

# 绘制游戏板
def draw_board():
    board_rect = pygame.Rect(MARGIN, MARGIN + 60, BOARD_SIZE, BOARD_SIZE)
    pygame.draw.rect(screen, BOARD_COLOR, board_rect, 0, 15)
    pygame.draw.rect(screen, (189, 195, 199), board_rect, 3, 15)
    
    # 绘制中心装饰
    draw_board_center()
    
    cell_size = BOARD_SIZE // 11  # 改回原来的计算方式
    
    # 先绘制所有格子
    for i in range(40):
        if i <= 10:  # 底边 (从右到左)
            x = MARGIN + BOARD_SIZE - (i + 1) * cell_size
            y = MARGIN + 60 + BOARD_SIZE - cell_size
            rotation = 0  # 文字正向
        elif i <= 20:  # 左边 (从下到上)
            x = MARGIN
            y = MARGIN + 60 + BOARD_SIZE - (i - 10 + 1) * cell_size
            rotation = 0  # 文字正向
        elif i <= 30:  # 上边 (从左到右)
            x = MARGIN + (i - 20) * cell_size
            y = MARGIN + 60
            rotation = 0  # 文字正向
        else:  # 右边 (从上到下)
            x = MARGIN + BOARD_SIZE - cell_size
            y = MARGIN + 60 + (i - 30) * cell_size
            rotation = 0  # 文字正向
        
        # 角落格子处理
        if i in [0, 10, 20, 30]:
            if i == 0:  # 起点 (右下角)
                x = MARGIN + BOARD_SIZE - cell_size
                y = MARGIN + 60 + BOARD_SIZE - cell_size
            elif i == 10:  # 监狱 (左下角)
                x = MARGIN
                y = MARGIN + 60 + BOARD_SIZE - cell_size
            elif i == 20:  # 免费停车 (左上角)
                x = MARGIN
                y = MARGIN + 60
            elif i == 30:  # 进监狱 (右上角)
                x = MARGIN + BOARD_SIZE - cell_size
                y = MARGIN + 60
        
        draw_property_cell(i, x, y, cell_size, rotation)
    
    # 最后绘制所有玩家头像
    avatar_font = pygame.font.SysFont('segoeuisymbol', min(20, cell_size // 3))
    for i, player in enumerate(game.players):
        if not player["bankrupt"]:
            # 计算玩家所在格子的位置
            pos = player["position"]
            if pos <= 10:  # 底边
                x = MARGIN + BOARD_SIZE - (pos + 1) * cell_size
                y = MARGIN + 60 + BOARD_SIZE - cell_size
            elif pos <= 20:  # 左边
                x = MARGIN
                y = MARGIN + 60 + BOARD_SIZE - (pos - 10 + 1) * cell_size
            elif pos <= 30:  # 上边
                x = MARGIN + (pos - 20) * cell_size
                y = MARGIN + 60
            else:  # 右边
                x = MARGIN + BOARD_SIZE - cell_size
                y = MARGIN + 60 + (pos - 30) * cell_size
            
            # 角落格子处理
            if pos in [0, 10, 20, 30]:
                if pos == 0:  # 起点
                    x = MARGIN + BOARD_SIZE - cell_size
                    y = MARGIN + 60 + BOARD_SIZE - cell_size
                elif pos == 10:  # 监狱
                    x = MARGIN
                    y = MARGIN + 60 + BOARD_SIZE - cell_size
                elif pos == 20:  # 免费停车
                    x = MARGIN
                    y = MARGIN + 60
                elif pos == 30:  # 进监狱
                    x = MARGIN + BOARD_SIZE - cell_size
                    y = MARGIN + 60
            
            # 计算头像位置，确保不同玩家的头像不重叠
            avatar_x = x + 10 + (i * 20)
            avatar_y = y + cell_size - 25
            
            # 绘制头像
            avatar_surface = avatar_font.render(PLAYER_AVATARS[i], True, PLAYER_COLORS[i])
            screen.blit(avatar_surface, (avatar_x, avatar_y))

def draw_start_cell(x, y, size):
    """绘制起点格子"""
    # 绘制GO格子的特殊样式
    cell_rect = pygame.Rect(x, y, size, size)
    pygame.draw.rect(screen, SPECIAL_CELL_COLORS["起点"], cell_rect, 0, 5)
    pygame.draw.rect(screen, (189, 195, 199), cell_rect, 1, 5)
    
    # 添加GO标志
    go_font = pygame.font.SysFont('arial', int(size * 0.5), bold=True)
    go_text = go_font.render("GO", True, (255, 255, 255))
    screen.blit(go_text, (x + size//2 - go_text.get_width()//2, y + size//4))
    
    # 添加箭头标志
    arrow_points = [
        (x + size//4, y + size//2),
        (x + size//2, y + size//4),
        (x + 3*size//4, y + size//2),
        (x + size//2, y + 3*size//4)
    ]
    pygame.draw.polygon(screen, (255, 255, 255), arrow_points)
    
    # 添加奖励提示
    bonus_text = font_small.render("+$200", True, (255, 255, 255))
    screen.blit(bonus_text, (x + size//2 - bonus_text.get_width()//2, y + 2*size//3))

def draw_board_center():
    # 计算中心区域
    center_x = MARGIN + BOARD_SIZE // 4
    center_y = MARGIN + 60 + BOARD_SIZE // 4
    center_width = BOARD_SIZE // 2
    center_height = BOARD_SIZE // 2
    
    # 绘制大富翁标志
    logo_font = pygame.font.SysFont('simhei', 60, bold=True)  # 减小logo大小
    logo_text = logo_font.render("大富翁", True, (52, 152, 219))
    screen.blit(logo_text, (center_x + center_width//2 - logo_text.get_width()//2, 
                           center_y + 20))  # 将logo移到顶部
    
    # 如果正在掷骰子或在监狱中，显示骰子
    if game.rolling_dice or (game.players[game.current_player]["in_jail"] and not game.game_over):
        dice_x = center_x + center_width//2 - 70
        dice_y = center_y + center_height//2 - 30
        
        # 绘制骰子背景
        pygame.draw.rect(screen, (70, 70, 70), (dice_x - 10, dice_y - 10, 160, 80), 0, 15)
        
        # 绘制骰子
        screen.blit(dice_images[game.dice_values[0] - 1], (dice_x, dice_y))
        screen.blit(dice_images[game.dice_values[1] - 1], (dice_x + 80, dice_y))
        
        if game.players[game.current_player]["in_jail"]:
            jail_text = font_medium.render("尝试出狱", True, (255, 255, 255))
            screen.blit(jail_text, (dice_x + 30, dice_y - 30))
    
    # 如果不在拍卖状态且游戏未结束，显示按钮
    if not game.game_over and not game.rolling_dice and game.auction_property is None:
        # 绘制骰子按钮
        dice_button_width = 120
        dice_button_height = 40
        dice_button_x = center_x + center_width//2 - dice_button_width - 10
        dice_button_y = center_y + center_height - 60
        
        dice_button_rect = pygame.Rect(dice_button_x, dice_button_y, dice_button_width, dice_button_height)
        
        # 判断骰子按钮是否可用
        can_roll_dice = (not game.has_rolled_dice or 
                        (game.dice_values[0] == game.dice_values[1] and game.double_count < 3))
        
        if can_roll_dice:
            pygame.draw.rect(screen, (52, 152, 219), dice_button_rect, 0, 10)
            pygame.draw.rect(screen, (41, 128, 185), dice_button_rect, 2, 10)
        else:
            pygame.draw.rect(screen, (149, 165, 166), dice_button_rect, 0, 10)
            pygame.draw.rect(screen, (127, 140, 141), dice_button_rect, 2, 10)
        
        dice_text = font_medium.render("掷骰子", True, (255, 255, 255))
        screen.blit(dice_text, (dice_button_x + dice_button_width//2 - dice_text.get_width()//2, 
                               dice_button_y + dice_button_height//2 - dice_text.get_height()//2))
        
        # 绘制结束回合按钮
        end_turn_button_width = 120
        end_turn_button_height = 40
        end_turn_button_x = center_x + center_width//2 + 10
        end_turn_button_y = center_y + center_height - 60
        
        end_turn_button_rect = pygame.Rect(end_turn_button_x, end_turn_button_y, end_turn_button_width, end_turn_button_height)
        
        # 判断结束回合按钮是否可用
        can_end_turn = (game.has_rolled_dice and 
                       not game.showing_purchase_choice and 
                       not game.selling_property and 
                       not game.show_rent_message and 
                       not game.show_card_message and
                       not (game.dice_values[0] == game.dice_values[1] and game.double_count < 3))
        
        if can_end_turn:
            pygame.draw.rect(screen, (231, 76, 60), end_turn_button_rect, 0, 10)
            pygame.draw.rect(screen, (192, 57, 43), end_turn_button_rect, 2, 10)
        else:
            pygame.draw.rect(screen, (149, 165, 166), end_turn_button_rect, 0, 10)
            pygame.draw.rect(screen, (127, 140, 141), end_turn_button_rect, 2, 10)
        
        end_turn_text = font_medium.render("结束回合", True, (255, 255, 255))
        screen.blit(end_turn_text, (end_turn_button_x + end_turn_button_width//2 - end_turn_text.get_width()//2, 
                                   end_turn_button_y + end_turn_button_height//2 - end_turn_text.get_height()//2))
        
        # 保存按钮位置供点击检测使用
        game.dice_button_rect = dice_button_rect
        game.end_turn_button_rect = end_turn_button_rect
        game.can_roll_dice = can_roll_dice
        game.can_end_turn = can_end_turn

def draw_debt_info():
    """绘制债务信息"""
    debt_bg = pygame.Rect(SCREEN_WIDTH // 2 - 200, 50, 400, 100)
    pygame.draw.rect(screen, (231, 76, 60), debt_bg, 0, 15)
    pygame.draw.rect(screen, (192, 57, 43), debt_bg, 3, 15)
    
    debt_text = font_large.render(f"当前债务: ${game.current_debt}", True, (255, 255, 255))
    screen.blit(debt_text, (SCREEN_WIDTH // 2 - debt_text.get_width() // 2, 60))
    
    if game.creditor:
        creditor_text = font_medium.render(f"债权人: {game.creditor['name']}", True, (255, 255, 255))
        screen.blit(creditor_text, (SCREEN_WIDTH // 2 - creditor_text.get_width() // 2, 100))

def draw_property_sale_ui():
    """绘制地产出售界面"""
    sale_bg = pygame.Rect(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 150, 500, 300)
    pygame.draw.rect(screen, (44, 62, 80), sale_bg, 0, 15)
    pygame.draw.rect(screen, (52, 152, 219), sale_bg, 3, 15)
    
    # 显示出售信息
    lines = game.message.split('\n')
    for i, line in enumerate(lines):
        text = font_medium.render(line, True, (255, 255, 255))
        screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 
                          SCREEN_HEIGHT // 2 - 120 + i * 30))

def draw_mortgage_ui():
    """绘制抵押界面"""
    mortgage_bg = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100, 400, 200)
    pygame.draw.rect(screen, (44, 62, 80), mortgage_bg, 0, 15)
    pygame.draw.rect(screen, (52, 152, 219), mortgage_bg, 3, 15)
    
    lines = game.message.split('\n')
    for i, line in enumerate(lines):
        text = font_medium.render(line, True, (255, 255, 255))
        screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 
                          SCREEN_HEIGHT // 2 - 70 + i * 30))

def draw_unmortgage_ui():
    """绘制取消抵押界面"""
    unmortgage_bg = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100, 400, 200)
    pygame.draw.rect(screen, (44, 62, 80), unmortgage_bg, 0, 15)
    pygame.draw.rect(screen, (52, 152, 219), unmortgage_bg, 3, 15)
    
    lines = game.message.split('\n')
    for i, line in enumerate(lines):
        text = font_medium.render(line, True, (255, 255, 255))
        screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 
                          SCREEN_HEIGHT // 2 - 70 + i * 30))

def draw_house_sale_ui():
    """绘制房屋出售界面"""
    sale_bg = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100, 400, 200)
    pygame.draw.rect(screen, (44, 62, 80), sale_bg, 0, 15)
    pygame.draw.rect(screen, (52, 152, 219), sale_bg, 3, 15)
    
    lines = game.message.split('\n')
    for i, line in enumerate(lines):
        text = font_medium.render(line, True, (255, 255, 255))
        screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 
                          SCREEN_HEIGHT // 2 - 70 + i * 30))

# 添加处理资金不足的函数
def handle_insufficient_funds(player, amount, creditor=None):
    """处理资金不足的情况"""
    game.current_debt = amount
    game.creditor = creditor
    
    # 计算玩家的总资产
    total_assets = player["money"]
    for prop_idx in player["properties"]:
        prop = game.properties[prop_idx]
        # 计算地产价值
        if not prop["mortgaged"]:
            total_assets += prop["price"]
        # 计算房屋价值
        if prop["hotel"]:
            total_assets += get_house_price(prop) * 2.5  # 酒店价值为房屋价格的2.5倍
        else:
            total_assets += prop["houses"] * get_house_price(prop)
    
    if total_assets < amount:
        # 如果总资产不足以支付，直接破产
        handle_bankruptcy(player, creditor)
        return False
    
    # 显示选项菜单
    game.message = f"资金不足! 需要支付{amount}元。请选择操作:\n" + \
                   "1. 出售地产(1键)\n" + \
                   "2. 抵押地产(2键)\n" + \
                   "3. 出售房屋(3键)\n" + \
                   "4. 宣布破产(4键)"
    return True

def get_house_price(prop):
    """获取房屋建造价格"""
    # 根据地产组确定房屋价格
    if prop["group"] in [0, 1]:  # 棕色和浅蓝色
        return 50
    elif prop["group"] in [2, 3]:  # 粉色和橙色
        return 100
    elif prop["group"] in [4, 5]:  # 红色和黄色
        return 150
    else:  # 绿色和蓝色
        return 200

def start_property_sale(player):
    """开始出售地产流程"""
    if not player["properties"]:
        game.message = "没有可出售的地产!"
        return
    
    game.selling_property = player["properties"][0]
    game.selling_price = game.properties[game.selling_property]["price"]
    game.selling_to = (game.current_player + 1) % len(game.players)
    while game.players[game.selling_to]["bankrupt"]:
        game.selling_to = (game.selling_to + 1) % len(game.players)
    
    update_sale_message()

def update_sale_message():
    """更新出售信息显示"""
    prop = game.properties[game.selling_property]
    seller = game.players[game.current_player]
    buyer = game.players[game.selling_to]
    game.message = f"{seller['name']}正在出售{prop['name']}\n" + \
                   f"当前价格: ${game.selling_price}\n" + \
                   f"潜在买家: {buyer['name']}\n" + \
                   "← →键选择地产, ↑↓键调整价格\n" + \
                   "Enter确认, Tab切换买家, ESC取消"

def handle_property_sale(key):
    """处理地产出售的按键操作"""
    player = game.players[game.current_player]
    
    if key == pygame.K_ESCAPE:
        game.selling_property = None
        return
    
    if key == pygame.K_TAB:
        # 切换买家
        game.selling_to = (game.selling_to + 1) % len(game.players)
        while game.selling_to == game.current_player or game.players[game.selling_to]["bankrupt"]:
            game.selling_to = (game.selling_to + 1) % len(game.players)
        update_sale_message()
        return
    
    if key == pygame.K_LEFT or key == pygame.K_RIGHT:
        # 切换要出售的地产
        current_index = player["properties"].index(game.selling_property)
        if key == pygame.K_LEFT:
            new_index = (current_index - 1) % len(player["properties"])
        else:
            new_index = (current_index + 1) % len(player["properties"])
        game.selling_property = player["properties"][new_index]
        game.selling_price = game.properties[game.selling_property]["price"]
        update_sale_message()
        return
    
    if key == pygame.K_UP:
        game.selling_price += 10
        update_sale_message()
    elif key == pygame.K_DOWN and game.selling_price > 10:
        game.selling_price -= 10
        update_sale_message()
    elif key == pygame.K_RETURN:
        # 确认交易
        buyer = game.players[game.selling_to]
        if buyer["money"] >= game.selling_price:
            complete_property_sale()
        else:
            game.message = f"{buyer['name']}资金不足，无法购买!"

def complete_property_sale():
    """完成地产交易"""
    seller = game.players[game.current_player]
    buyer = game.players[game.selling_to]
    prop = game.properties[game.selling_property]
    
    # 转移资金
    seller["money"] += game.selling_price
    buyer["money"] -= game.selling_price
    
    # 转移地产
    seller["properties"].remove(game.selling_property)
    buyer["properties"].append(game.selling_property)
    prop["owner"] = game.selling_to
    
    game.message = f"{seller['name']}将{prop['name']}以${game.selling_price}卖给了{buyer['name']}"
    
    # 检查是否有足够的钱支付债务
    if game.current_debt > 0 and seller["money"] >= game.current_debt:
        pay_debt(seller)
    
    game.selling_property = None

def start_mortgage(player):
    """开始抵押地产流程"""
    if not player["properties"]:
        game.message = "没有可抵押的地产!"
        return
    
    unmortgaged_properties = [p for p in player["properties"] 
                            if not game.properties[p]["mortgaged"]]
    if not unmortgaged_properties:
        game.message = "没有可抵押的地产!"
        return
    
    game.mortgage_mode = True
    game.selling_property = unmortgaged_properties[0]
    update_mortgage_message()

def update_mortgage_message():
    """更新抵押信息显示"""
    prop = game.properties[game.selling_property]
    mortgage_value = prop["price"] // 2
    game.message = f"选择要抵押的地产: {prop['name']}\n" + \
                   f"抵押价值: ${mortgage_value}\n" + \
                   "← →键选择地产, Enter确认, ESC取消"

def handle_mortgage(key):
    """处理抵押操作的按键"""
    player = game.players[game.current_player]
    
    if key == pygame.K_ESCAPE:
        game.mortgage_mode = False
        game.selling_property = None
        return
    
    if key == pygame.K_LEFT or key == pygame.K_RIGHT:
        # 切换要抵押的地产
        unmortgaged_properties = [p for p in player["properties"] 
                                if not game.properties[p]["mortgaged"]]
        current_index = unmortgaged_properties.index(game.selling_property)
        if key == pygame.K_LEFT:
            new_index = (current_index - 1) % len(unmortgaged_properties)
        else:
            new_index = (current_index + 1) % len(unmortgaged_properties)
        game.selling_property = unmortgaged_properties[new_index]
        update_mortgage_message()
    
    elif key == pygame.K_RETURN:
        # 确认抵押
        prop = game.properties[game.selling_property]
        mortgage_value = prop["price"] // 2
        player["money"] += mortgage_value
        prop["mortgaged"] = True
        game.message = f"{player['name']}抵押了{prop['name']}，获得${mortgage_value}"
        
        # 检查是否有足够的钱支付债务
        if game.current_debt > 0 and player["money"] >= game.current_debt:
            pay_debt(player)
        
        game.mortgage_mode = False
        game.selling_property = None

def start_unmortgage(player):
    """开始取消抵押流程"""
    mortgaged_properties = [p for p in player["properties"] 
                          if game.properties[p]["mortgaged"]]
    if not mortgaged_properties:
        game.message = "没有已抵押的地产!"
        return
    
    game.unmortgage_mode = True
    game.selling_property = mortgaged_properties[0]
    update_unmortgage_message()

def update_unmortgage_message():
    """更新取消抵押信息显示"""
    prop = game.properties[game.selling_property]
    unmortgage_cost = int(prop["price"] * 0.55)  # 赎回成本为抵押价值+10%利息
    game.message = f"选择要赎回的地产: {prop['name']}\n" + \
                   f"赎回成本: ${unmortgage_cost}\n" + \
                   "← →键选择地产, Enter确认, ESC取消"

def handle_unmortgage(key):
    """处理取消抵押操作的按键"""
    player = game.players[game.current_player]
    
    if key == pygame.K_ESCAPE:
        game.unmortgage_mode = False
        game.selling_property = None
        return
    
    if key == pygame.K_LEFT or key == pygame.K_RIGHT:
        # 切换要赎回的地产
        mortgaged_properties = [p for p in player["properties"] 
                              if game.properties[p]["mortgaged"]]
        current_index = mortgaged_properties.index(game.selling_property)
        if key == pygame.K_LEFT:
            new_index = (current_index - 1) % len(mortgaged_properties)
        else:
            new_index = (current_index + 1) % len(mortgaged_properties)
        game.selling_property = mortgaged_properties[new_index]
        update_unmortgage_message()
    
    elif key == pygame.K_RETURN:
        # 确认赎回
        prop = game.properties[game.selling_property]
        unmortgage_cost = int(prop["price"] * 0.55)
        if player["money"] >= unmortgage_cost:
            player["money"] -= unmortgage_cost
            prop["mortgaged"] = False
            game.message = f"{player['name']}赎回了{prop['name']}，支付${unmortgage_cost}"
            game.unmortgage_mode = False
            game.selling_property = None
        else:
            game.message = "资金不足，无法赎回地产!"

def start_selling_houses(player):
    """开始出售房屋流程"""
    properties_with_buildings = [p for p in player["properties"] 
                               if game.properties[p]["houses"] > 0 or 
                               game.properties[p]["hotel"]]
    if not properties_with_buildings:
        game.message = "没有可出售的房屋或酒店!"
        return
    
    game.selling_houses = True
    game.selling_property = properties_with_buildings[0]
    update_house_sale_message()

def update_house_sale_message():
    """更新房屋出售信息显示"""
    prop = game.properties[game.selling_property]
    house_price = get_house_price(prop) // 2  # 出售价格为建造价格的一半
    
    if prop["hotel"]:
        building_text = "酒店"
        sale_value = house_price * 5
    else:
        building_text = f"{prop['houses']}座房屋"
        sale_value = house_price * prop["houses"]
    
    game.message = f"选择要出售建筑的地产: {prop['name']}\n" + \
                   f"当前建筑: {building_text}\n" + \
                   f"出售价值: ${sale_value}\n" + \
                   "← →键选择地产, ↑↓键选择数量\n" + \
                   "Enter确认, ESC取消"

def handle_house_sale(key):
    """处理房屋出售操作的按键"""
    player = game.players[game.current_player]
    prop = game.properties[game.selling_property]
    
    if key == pygame.K_ESCAPE:
        game.selling_houses = False
        game.selling_property = None
        return
    
    if key == pygame.K_LEFT or key == pygame.K_RIGHT:
        # 切换地产
        properties_with_buildings = [p for p in player["properties"] 
                                   if game.properties[p]["houses"] > 0 or 
                                   game.properties[p]["hotel"]]
        current_index = properties_with_buildings.index(game.selling_property)
        if key == pygame.K_LEFT:
            new_index = (current_index - 1) % len(properties_with_buildings)
        else:
            new_index = (current_index + 1) % len(properties_with_buildings)
        game.selling_property = properties_with_buildings[new_index]
        update_house_sale_message()
    
    elif key == pygame.K_UP or key == pygame.K_DOWN:
        # 增减要出售的房屋数量
        if prop["hotel"]:
            # 如果是酒店，转换为4座房屋
            prop["hotel"] = False
            prop["houses"] = 4
        elif key == pygame.K_DOWN and prop["houses"] > 0:
            prop["houses"] -= 1
        elif key == pygame.K_UP and prop["houses"] < 4:
            prop["houses"] += 1
        update_house_sale_message()
    
    elif key == pygame.K_RETURN:
        # 确认出售
        house_price = get_house_price(prop) // 2
        if prop["hotel"]:
            sale_value = house_price * 5
            prop["hotel"] = False
            prop["houses"] = 0
        else:
            sale_value = house_price * prop["houses"]
            prop["houses"] = 0
        
        player["money"] += sale_value
        game.message = f"{player['name']}出售了建筑，获得${sale_value}"
        
        # 检查是否有足够的钱支付债务
        if game.current_debt > 0 and player["money"] >= game.current_debt:
            pay_debt(player)
        
        game.selling_houses = False
        game.selling_property = None

def pay_debt(player):
    """支付债务"""
    if game.creditor:
        # 支付给其他玩家
        game.creditor["money"] += game.current_debt
    player["money"] -= game.current_debt
    game.message = f"{player['name']}支付了${game.current_debt}的债务"
    game.current_debt = 0
    game.creditor = None

# 添加绘制租金消息的函数
def draw_rent_message():
    # 创建半透明背景
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))
    screen.blit(overlay, (0, 0))
    
    # 创建消息框
    msg_width = 400
    msg_height = 150
    msg_x = SCREEN_WIDTH // 2 - msg_width // 2
    msg_y = SCREEN_HEIGHT // 2 - msg_height // 2
    
    pygame.draw.rect(screen, (44, 62, 80), (msg_x, msg_y, msg_width, msg_height), 0, 15)
    pygame.draw.rect(screen, (52, 152, 219), (msg_x, msg_y, msg_width, msg_height), 3, 15)
    
    # 显示租金信息
    lines = wrap_text(game.rent_message, font_medium, msg_width - 40)
    for i, line in enumerate(lines):
        text = font_medium.render(line, True, (255, 255, 255))
        screen.blit(text, (msg_x + 20, msg_y + 20 + i * 30))
    
    # 显示继续提示
    continue_text = font_small.render("按空格键继续", True, (200, 200, 200))
    screen.blit(continue_text, (msg_x + msg_width//2 - continue_text.get_width()//2, 
                               msg_y + msg_height - 30))

def draw_card_message():
    """绘制卡片消息"""
    # 创建半透明背景
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))
    screen.blit(overlay, (0, 0))
    
    # 创建卡片
    card_width = 400
    card_height = 300
    card_x = SCREEN_WIDTH // 2 - card_width // 2
    card_y = SCREEN_HEIGHT // 2 - card_height // 2
    
    # 根据卡片类型选择颜色
    if game.card_type == "机会":
        card_color = SPECIAL_CELL_COLORS["机会"]
        card_icon = "?"
    else:  # 命运
        card_color = SPECIAL_CELL_COLORS["命运"]
        card_icon = "★"
    
    # 绘制卡片背景
    card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
    pygame.draw.rect(screen, card_color, card_rect, 0, 15)
    pygame.draw.rect(screen, (255, 255, 255), card_rect, 3, 15)
    
    # 绘制卡片标题
    title = font_large.render(game.card_type, True, (255, 255, 255))
    screen.blit(title, (card_x + card_width//2 - title.get_width()//2, card_y + 20))
    
    # 绘制卡片图标
    icon_font = pygame.font.SysFont('arial', 60, bold=True)
    icon = icon_font.render(card_icon, True, (255, 255, 255))
    screen.blit(icon, (card_x + card_width//2 - icon.get_width()//2, card_y + 60))
    
    # 绘制卡片内容
    lines = wrap_text(game.card_message, font_medium, card_width - 40)
    for i, line in enumerate(lines):
        text = font_medium.render(line, True, (255, 255, 255))
        screen.blit(text, (card_x + 20, card_y + 140 + i * 30))
    
    # 绘制提示
    hint = font_small.render("按空格键继续", True, (200, 200, 200))
    screen.blit(hint, (card_x + card_width//2 - hint.get_width()//2, 
                      card_y + card_height - 30))

def find_next_player_to_bid():
    """找到下一个可以竞价的玩家（状态为pending或bidding）"""
    start_idx = (game.auction_player + 1) % len(game.players)
    current_idx = start_idx
    
    while True:
        if (not game.players[current_idx]["bankrupt"] and 
            game.auction_status.get(current_idx) in ["pending", "bidding"]):
            return current_idx
        
        current_idx = (current_idx + 1) % len(game.players)
        if current_idx == start_idx:
            return None

def draw_property_cell(index, x, y, size, rotation):
    prop = game.properties[index]
    
    # 特殊处理起点格子
    if prop["name"] == "起点":
        draw_start_cell(x, y, size)
        return
    
    # 获取格子颜色
    if prop["name"] in SPECIAL_CELL_COLORS:
        cell_color = SPECIAL_CELL_COLORS[prop["name"]]
        use_white_bg = False
    elif prop["group"] >= 0:
        cell_color = PROPERTY_COLORS[prop["group"]]
        use_white_bg = True
    else:
        cell_color = CELL_COLOR
        use_white_bg = False
    
    # 绘制格子背景
    cell_rect = pygame.Rect(x, y, size, size)
    pygame.draw.rect(screen, CELL_COLOR if use_white_bg else cell_color, cell_rect, 0, 5)
    pygame.draw.rect(screen, (189, 195, 199), cell_rect, 1, 5)
    
    # 确定色条位置和宽度
    color_bar_width = size // 8  # 更窄的色条
    
    # 根据格子在棋盘上的位置确定色条位置
    board_x = x - MARGIN
    board_y = y - (MARGIN + 60)  # 考虑标题栏的偏移
    
    if use_white_bg:
        if board_y <= 0:  # 上边
            # 色条在下面
            color_bar_rect = pygame.Rect(x, y + size - color_bar_width, size, color_bar_width)
        elif board_y >= BOARD_SIZE - size:  # 下边
            # 色条在上面
            color_bar_rect = pygame.Rect(x, y, size, color_bar_width)
        elif board_x <= 0:  # 左边
            # 色条在右边
            color_bar_rect = pygame.Rect(x + size - color_bar_width, y, color_bar_width, size)
        else:  # 右边
            # 色条在左边
            color_bar_rect = pygame.Rect(x, y, color_bar_width, size)
        
        pygame.draw.rect(screen, cell_color, color_bar_rect, 0, 5)
        
        # 填充圆角部分
        if board_y <= 0:  # 上边
            pygame.draw.rect(screen, cell_color, (x, y + size - color_bar_width, size, color_bar_width - 5))
        elif board_y >= BOARD_SIZE - size:  # 下边
            pygame.draw.rect(screen, cell_color, (x, y + 5, size, color_bar_width - 5))
        elif board_x <= 0:  # 左边
            pygame.draw.rect(screen, cell_color, (x + size - color_bar_width, y, color_bar_width - 5, size))
        else:  # 右边
            pygame.draw.rect(screen, cell_color, (x + 5, y, color_bar_width - 5, size))
    
    # 创建文字表面
    text_surface = pygame.Surface((size - 4, size - 4), pygame.SRCALPHA)
    
    # 根据格子大小动态调整字体大小
    name_font = pygame.font.SysFont('simhei', min(14, size // 5))
    price_font = pygame.font.SysFont('simhei', min(12, size // 6))
    icon_font = pygame.font.SysFont('segoeuisymbol', min(16, size // 4))
    
    # 计算文字和其他元素的布局
    name_lines = wrap_text(prop["name"], name_font, size - 20)  # 减小文本宽度以确保不会太靠近边缘
    
    # 计算所有元素的总高度
    total_height = len(name_lines) * (name_font.get_height() + 2)
    if prop["group"] in [-2, -3]:  # 如果有图标
        total_height += icon_font.get_height() + 2
    if prop["price"] > 0:  # 如果有价格
        total_height += price_font.get_height() + 2
    
    # 计算内容区域的可用高度
    if use_white_bg:
        if board_y <= 0 or board_y >= BOARD_SIZE - size:  # 上边或下边
            available_height = size - color_bar_width
        else:  # 左边或右边
            available_height = size
    else:
        available_height = size
    
    # 计算内容的起始Y坐标，确保垂直居中
    content_start_y = (available_height - total_height) // 2
    
    # 如果是底边的格子，需要考虑色条在顶部
    if board_y >= BOARD_SIZE - size and use_white_bg:
        content_start_y += color_bar_width
    
    # 绘制名称
    current_y = content_start_y
    for line in name_lines:
        line_surface = name_font.render(line, True, TEXT_COLOR)
        text_surface.blit(line_surface, 
            ((size - line_surface.get_width()) // 2, current_y))
        current_y += name_font.get_height() + 2
    
    # 绘制图标（如果有）
    if prop["group"] == -2:  # 铁路
        icon = icon_font.render("🚂", True, TEXT_COLOR)
        text_surface.blit(icon, ((size - icon.get_width()) // 2, current_y))
        current_y += icon_font.get_height() + 2
    elif prop["group"] == -3:  # 公共事业
        icon = icon_font.render("💡", True, TEXT_COLOR)
        text_surface.blit(icon, ((size - icon.get_width()) // 2, current_y))
        current_y += icon_font.get_height() + 2
    
    # 绘制价格（如果有）
    if prop["price"] > 0:
        price_surface = price_font.render(f"${prop['price']}", True, (39, 174, 96))
        text_surface.blit(price_surface, 
            ((size - price_surface.get_width()) // 2, current_y))
    
    # 绘制所有者标记（如果有）
    if prop["owner"] is not None:
        owner_idx = prop["owner"]
        owner_color = PLAYER_COLORS[owner_idx]  # 使用玩家颜色
        owner_x = 5
        owner_y = 5
        pygame.draw.circle(text_surface, owner_color, (owner_x, owner_y), 6)
        
        if prop["houses"] > 0 or prop["hotel"]:
            house_x = owner_x + 15
            house_y = owner_y
            if prop["hotel"]:
                hotel_surface = price_font.render("酒", True, owner_color)  # 使用所有者颜色
                text_surface.blit(hotel_surface, (house_x, house_y - 5))
            else:
                houses_text = str(prop["houses"])
                houses_surface = price_font.render(houses_text, True, owner_color)  # 使用所有者颜色
                text_surface.blit(houses_surface, (house_x, house_y - 5))
    
    # 放置最终的文字表面
    screen.blit(text_surface, (x + 2, y + 2))

# 绘制玩家信息
def draw_player_info():
    info_x = MARGIN * 2 + BOARD_SIZE
    info_width = SCREEN_WIDTH - info_x - MARGIN
    
    for i, player in enumerate(game.players):
        y = MARGIN + 60 + i * 200  # 增加玩家信息框的高度
        
        # 玩家信息背景
        player_bg = pygame.Rect(info_x, y, info_width - 20, 190)
        bg_color = (PLAYER_COLORS[i][0] // 2, PLAYER_COLORS[i][1] // 2, PLAYER_COLORS[i][2] // 2)
        pygame.draw.rect(screen, bg_color, player_bg, 0, 10)
        pygame.draw.rect(screen, PLAYER_COLORS[i], player_bg, 2, 10)
        
        # 当前玩家高亮
        if i == game.current_player:
            pygame.draw.rect(screen, (255, 255, 255), player_bg, 3, 10)
        
        # 破产标记
        if player["bankrupt"]:
            bankrupt_surface = font_large.render("破产", True, (231, 76, 60))
            screen.blit(bankrupt_surface, (info_x + info_width - 100, y + 10))
        
        # 玩家标题
        title = f"{player['name']}"
        title_surface = font_large.render(title, True, (255, 255, 255))
        screen.blit(title_surface, (info_x + 10, y + 10))
        
        # 玩家资金
        money_text = f"资金: ${player['money']}"
        money_surface = font_medium.render(money_text, True, (255, 255, 255))
        screen.blit(money_surface, (info_x + 10, y + 45))
        
        # 玩家位置
        pos_text = f"位置: {game.properties[player['position']]['name']}"
        pos_surface = font_medium.render(pos_text, True, (255, 255, 255))
        screen.blit(pos_surface, (info_x + 10, y + 75))
        
        # 显示拥有的地产列表
        if not player["bankrupt"] and player["properties"]:
            props_y = y + 105
            props_text = font_medium.render(f"拥有地产({len(player['properties'])}个):", True, (255, 255, 255))
            screen.blit(props_text, (info_x + 10, props_y))
            
            # 按颜色分组排序地产
            grouped_props = {}
            for prop_idx in player["properties"]:
                prop = game.properties[prop_idx]
                group = prop["group"]
                if group not in grouped_props:
                    grouped_props[group] = []
                grouped_props[group].append(prop)
            
            # 按组号排序
            sorted_groups = sorted(grouped_props.keys())
            
            # 分三列显示地产
            col_width = (info_width - 40) // 3
            current_y = props_y + 25
            current_x = info_x + 10
            max_y = y + 180
            
            for group in sorted_groups:
                for prop in grouped_props[group]:
                    if current_y > max_y:
                        current_y = props_y + 25
                        current_x += col_width
                        if current_x >= info_x + info_width - col_width:
                            break
                    
                    prop_text = prop["name"]
                    if prop["hotel"]:
                        prop_text += " (酒店)"
                    elif prop["houses"] > 0:
                        prop_text += f" ({prop['houses']}房)"
                    if prop["mortgaged"]:
                        prop_text += " (抵押)"
                    
                    color = PROPERTY_COLORS[group] if group >= 0 else (200, 200, 200)
                    prop_surface = font_small.render(prop_text, True, color)
                    if current_x + prop_surface.get_width() > info_x + current_x + col_width - 10:
                        prop_text = prop_text[:8] + "..."
                        prop_surface = font_small.render(prop_text, True, color)
                    screen.blit(prop_surface, (current_x, current_y))
                    current_y += 20

# 处理购买选择
def handle_purchase_choice(choice):
    if not game.showing_purchase_choice:
        return
    
    player = game.players[game.current_player]
    prop = game.purchase_property
    
    if choice == "Y":
        if player["money"] >= prop["price"]:
            buy_property(player, prop)
        else:
            game.message = f"资金不足无法购买{prop['name']}"
            start_auction(prop)
    else:
        start_auction(prop)
    
    game.showing_purchase_choice = False
    game.purchase_property = None

# 在draw_game函数中添加购买选择界面的绘制
def draw_purchase_choice():
    if not game.showing_purchase_choice:
        return
    
    prop = game.purchase_property
    player = game.players[game.current_player]
    
    # 创建选择框
    dialog_width = 400
    dialog_height = 200
    dialog_x = SCREEN_WIDTH // 2 - dialog_width // 2
    dialog_y = SCREEN_HEIGHT // 2 - dialog_height // 2
    
    # 绘制半透明背景
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))
    screen.blit(overlay, (0, 0))
    
    # 绘制对话框
    dialog_bg = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
    pygame.draw.rect(screen, (44, 62, 80), dialog_bg, 0, 15)
    pygame.draw.rect(screen, (52, 152, 219), dialog_bg, 3, 15)
    
    # 显示地产信息
    title = font_large.render(prop["name"], True, (255, 255, 255))
    screen.blit(title, (dialog_x + dialog_width // 2 - title.get_width() // 2, dialog_y + 20))
    
    price = font_medium.render(f"价格: ${prop['price']}", True, (46, 204, 113))
    screen.blit(price, (dialog_x + dialog_width // 2 - price.get_width() // 2, dialog_y + 60))
    
    rent = font_medium.render(f"租金: ${prop['rent']}", True, (231, 76, 60))
    screen.blit(rent, (dialog_x + dialog_width // 2 - rent.get_width() // 2, dialog_y + 90))
    
    money = font_medium.render(f"当前资金: ${player['money']}", True, (255, 255, 255))
    screen.blit(money, (dialog_x + dialog_width // 2 - money.get_width() // 2, dialog_y + 120))
    
    # 显示选项
    options = font_medium.render("按Y购买 / N拍卖", True, (255, 255, 255))
    screen.blit(options, (dialog_x + dialog_width // 2 - options.get_width() // 2, dialog_y + 160))

def handle_owned_property(player, prop):
    """处理玩家到达他人地产的情况"""
    owner = game.players[prop["owner"]]
    if owner["bankrupt"]:
        return
    
    # 计算租金
    rent = prop["rent"]
    
    # 如果是铁路，根据拥有的铁路数量增加租金
    if prop["group"] == -2:
        railroads = len([p for p in owner["properties"] if game.properties[p]["group"] == -2])
        rent = 25 * (2 ** (railroads - 1))
    
    # 如果是公用事业，根据骰子点数和拥有的公用事业数量计算租金
    elif prop["group"] == -3:
        utilities = len([p for p in owner["properties"] if game.properties[p]["group"] == -3])
        dice_total = sum(game.dice_values)
        rent = dice_total * (4 if utilities == 1 else 10)
    
    # 如果是普通地产，根据房屋数量增加租金
    else:
        if prop["hotel"]:
            rent *= 5
        elif prop["houses"] > 0:
            rent *= (1 + prop["houses"])
        
        # 如果拥有同一颜色的所有地产，基础租金翻倍
        if prop["group"] >= 0:
            same_group = [p for p in range(len(game.properties)) 
                         if game.properties[p]["group"] == prop["group"]]
            if all(p in owner["properties"] for p in same_group):
                rent *= 2
    
    # 支付租金
    if player["money"] >= rent:
        player["money"] -= rent
        owner["money"] += rent
        game.message = f"{player['name']}支付{rent}元租金给{owner['name']}"
    else:
        game.message = f"{player['name']}无法支付{rent}元租金，破产!"
        handle_bankruptcy(player, owner)

if __name__ == "__main__":
    main()