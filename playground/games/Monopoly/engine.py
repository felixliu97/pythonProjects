"""
engine.py - 大富翁游戏引擎（完整规则 + 存档/读档支持）

游戏阶段 (phase):
  WAIT_FOR_ROLL   - 等待当前玩家掷骰子
  DECIDE_BUY      - 玩家选择是否购买当前地块
  GAME_OVER       - 游戏结束，只剩一位玩家
"""
import random
import json
import os
from models import Bank, Player, PropertySpace, TaxSpace, ActionSpace, CardSpace


class MonopolyEngine:
    def __init__(self, players):
        self.players = players
        self.current_player_index = 0
        from board_data import get_board_spaces, get_chance_cards, get_community_chest_cards
        self.board = get_board_spaces()
        self.chance_cards = get_chance_cards()
        self.community_chest_cards = get_community_chest_cards()
        random.shuffle(self.chance_cards)
        random.shuffle(self.community_chest_cards)
        self.chance_discard = []
        self.chest_discard = []
        self.bank = Bank()
        self.doubles_count = 0
        self.last_dice = (0, 0)
        self.logs = []
        self.phase = "WAIT_FOR_ROLL"
        self.winner = None

    # ─────────────────────────────── 日志 ────────────────────────────────────

    def log(self, msg):
        self.logs.append(msg)

    # ──────────────────────────── 回合控制 ───────────────────────────────────

    def current_player(self):
        return self.players[self.current_player_index]

    def active_players(self):
        return [p for p in self.players if not p.is_bankrupt]

    def next_turn(self):
        active = self.active_players()
        if len(active) == 1:
            self.winner = active[0]
            self.phase = "GAME_OVER"
            self.log(f"🏆 {self.winner.name} 赢得了游戏！")
            return

        self.doubles_count = 0
        while True:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            if not self.current_player().is_bankrupt:
                break

        self.phase = "WAIT_FOR_ROLL"
        self.log(f"━━ 轮到 {self.current_player().name} ━━")

    def roll_dice(self):
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        return d1, d2

    # ──────────────────────────── 回合主流程 ─────────────────────────────────

    def execute_turn(self):
        """执行当前玩家的掷骰+移动周期。"""
        player = self.current_player()
        if self.phase != "WAIT_FOR_ROLL":
            return

        # ── 监狱处理 ──────────────────────────────────────
        if player.in_jail:
            d1, d2 = self.roll_dice()
            self.last_dice = (d1, d2)
            total = d1 + d2
            is_double = d1 == d2

            if is_double:
                self.log(f"{player.name} 掷出双骰（{d1},{d2}），成功越狱！")
                player.in_jail = False
                player.jail_turns = 0
                passed_go = player.move(total)
                if passed_go:
                    player.add_money(200)
                    self.log(f"{player.name} 经过起点，收取 $200。")
                space = self.board[player.position]
                self.log(f"{player.name} 停在【{space.name}】。")
                self.resolve_space(player, space, total)
                if self.phase == "WAIT_FOR_ROLL":
                    self.next_turn()
            else:
                player.jail_turns += 1
                self.log(f"{player.name} 掷出（{d1},{d2}），未能越狱。狱中第 {player.jail_turns}/3 回合。")
                if player.jail_turns >= 3:
                    self.log(f"{player.name} 第三次未掷出双骰，强制缴纳 $50 保释金出狱。")
                    self._pay_bail(player, d1 + d2)
                else:
                    self.next_turn()
            return

        # ── 正常掷骰 ──────────────────────────────────────
        d1, d2 = self.roll_dice()
        self.last_dice = (d1, d2)
        total = d1 + d2
        is_double = d1 == d2
        self.log(f"{player.name} 掷出 🎲 {d1} + {d2} = {total}{'  （双骰！）' if is_double else ''}。")

        if is_double:
            self.doubles_count += 1
            if self.doubles_count >= 3:
                self.log(f"连续三次双骰！{player.name} 被送进监狱！")
                self.send_to_jail(player)
                self.next_turn()
                return

        passed_go = player.move(total)
        if passed_go:
            player.add_money(200)
            self.log(f"{player.name} 经过起点，收取 $200。")

        space = self.board[player.position]
        self.log(f"{player.name} 停在：【{space.name}】。")
        self.resolve_space(player, space, total)

        if self.phase == "WAIT_FOR_ROLL" and not is_double:
            self.next_turn()
        elif self.phase == "WAIT_FOR_ROLL" and is_double:
            self.log(f"{player.name} 掷出双骰，可以再掷一次！")

    def _pay_bail(self, player, dice_total):
        """支付 $50 出狱（强制或自愿）。"""
        player.pay_money(50)
        player.in_jail = False
        player.jail_turns = 0
        passed_go = player.move(dice_total)
        if passed_go:
            player.add_money(200)
            self.log(f"{player.name} 经过起点，收取 $200。")
        space = self.board[player.position]
        self.log(f"{player.name} 停在：【{space.name}】。")
        self.resolve_space(player, space, dice_total)
        if self.phase == "WAIT_FOR_ROLL":
            self.next_turn()

    def pay_bail_voluntary(self):
        """玩家主动支付 $50 保释金出狱。"""
        player = self.current_player()
        if not player.in_jail or self.phase != "WAIT_FOR_ROLL":
            return
        if not player.can_afford(50):
            self.log(f"{player.name} 没有足够的钱支付 $50 保释金！")
            return
        self.log(f"{player.name} 主动缴纳 $50 保释金出狱。")
        d1, d2 = self.roll_dice()
        self.last_dice = (d1, d2)
        total = d1 + d2
        self.log(f"{player.name} 掷出（{d1},{d2}）= {total}。")
        player.pay_money(50)
        player.in_jail = False
        player.jail_turns = 0
        passed_go = player.move(total)
        if passed_go:
            player.add_money(200)
            self.log(f"{player.name} 经过起点，收取 $200。")
        space = self.board[player.position]
        self.log(f"{player.name} 停在：【{space.name}】。")
        self.resolve_space(player, space, total)
        if self.phase == "WAIT_FOR_ROLL":
            self.next_turn()

    def use_jail_card(self):
        """使用出狱卡。"""
        player = self.current_player()
        if not player.in_jail or player.get_out_of_jail_free_cards <= 0:
            return
        player.get_out_of_jail_free_cards -= 1
        player.in_jail = False
        player.jail_turns = 0
        self.log(f"{player.name} 使用了免死金牌（出狱卡）！")
        self.execute_turn()

    # ──────────────────────────── 格子结算 ───────────────────────────────────

    def send_to_jail(self, player):
        self.log(f"{player.name} 被送进监狱！")
        player.position = 10
        player.in_jail = True
        player.jail_turns = 0
        self.doubles_count = 0

    def resolve_space(self, player, space, dice_roll):
        if isinstance(space, PropertySpace):
            self._resolve_property(player, space, dice_roll)
        elif isinstance(space, TaxSpace):
            self.log(f"{player.name} 缴纳 ${space.tax_amount} 税款。")
            self._charge_player(player, space.tax_amount, None)
        elif isinstance(space, ActionSpace):
            self._resolve_action(player, space)
        elif isinstance(space, CardSpace):
            self._resolve_card(player, space, dice_roll)

    def _resolve_property(self, player, space, dice_roll):
        if space.owner is None:
            self.log(f"【{space.name}】无主，售价：${space.price}。")
            if player.is_ai:
                self.ai_decide_buy(player, space)
            else:
                self.phase = "DECIDE_BUY"
        elif space.owner == player:
            self.log(f"{player.name} 停在自己的【{space.name}】上。")
        elif space.is_mortgaged:
            self.log(f"【{space.name}】已被抵押，无需支付租金。")
        else:
            rent = space.get_rent(self.board, dice_roll)
            self.log(f"{player.name} 向 {space.owner.name} 支付【{space.name}】租金 ${rent}。")
            self._charge_player(player, rent, space.owner)

    def _resolve_action(self, player, space):
        if space.action_type == "GO":
            player.add_money(200)
            self.log(f"{player.name} 停在起点，收取 $200。")
        elif space.action_type == "Go To Jail":
            self.send_to_jail(player)
        elif space.action_type == "Free Parking":
            self.log(f"{player.name} 停在免费停车场，休息一下。")
        elif space.action_type == "Jail":
            self.log(f"{player.name} 是来探监的，安全无事。")

    def _resolve_card(self, player, space, dice_roll):
        is_chance = space.card_type == "Chance"
        deck = self.chance_cards if is_chance else self.community_chest_cards
        discard = self.chance_discard if is_chance else self.chest_discard
        deck_name = "机会" if is_chance else "命运"

        if not deck:
            deck.extend(discard)
            discard.clear()
            random.shuffle(deck)

        card = deck.pop(0)
        self.log(f"📋 {player.name} 抽到【{deck_name}卡】：「{card.text}」")
        self._apply_card(player, card, dice_roll)

        if card.action_type != "get_out_of_jail_free":
            discard.append(card)

    def _apply_card(self, player, card, dice_roll):
        t = card.action_type
        p = card.params

        if t == "move_to":
            target = p["target"]
            if player.position > target and target != 0:
                player.add_money(200)
                self.log(f"{player.name} 经过起点，收取 $200。")
            elif player.position > 0 and target == 0:
                player.add_money(200)
                self.log(f"{player.name} 经过起点，收取 $200。")
            player.position = target
            space = self.board[target]
            self.log(f"{player.name} 移动到【{space.name}】。")
            self.resolve_space(player, space, dice_roll)

        elif t == "move_nearest":
            target_type = p["target_type"]
            type_name = "铁路" if target_type == "Station" else "公共事业"
            original = player.position
            for offset in range(1, 40):
                candidate = (original + offset) % 40
                sp = self.board[candidate]
                if isinstance(sp, PropertySpace) and sp.color == target_type:
                    if original > candidate:
                        player.add_money(200)
                        self.log(f"{player.name} 经过起点，收取 $200。")
                    player.position = candidate
                    self.log(f"{player.name} 移动到最近的{type_name}：【{sp.name}】。")
                    if sp.owner and sp.owner != player:
                        multiplier = p.get("multiplier", 1)
                        dm = p.get("dice_multiplier", 0)
                        if dm:
                            rent = dice_roll * dm
                        else:
                            base = sp.get_rent(self.board, dice_roll)
                            rent = base * multiplier
                        self.log(f"{player.name} 支付特殊租金 ${rent} 给 {sp.owner.name}。")
                        self._charge_player(player, rent, sp.owner)
                    elif sp.owner is None:
                        if player.is_ai:
                            self.ai_decide_buy(player, sp)
                        else:
                            self.phase = "DECIDE_BUY"
                    break

        elif t == "move_relative":
            steps = p["steps"]
            player.position = (player.position + steps) % 40
            space = self.board[player.position]
            self.log(f"{player.name} 后退 {abs(steps)} 步，停在【{space.name}】。")
            self.resolve_space(player, space, dice_roll)

        elif t == "go_to_jail":
            self.send_to_jail(player)

        elif t == "get_out_of_jail_free":
            player.get_out_of_jail_free_cards += 1
            self.log(f"{player.name} 获得一张免死金牌（出狱卡）。")

        elif t == "receive":
            amount = p["amount"]
            player.add_money(amount)
            self.log(f"{player.name} 收取 ${amount}。")

        elif t == "pay":
            amount = p["amount"]
            self.log(f"{player.name} 支付 ${amount}。")
            self._charge_player(player, amount, None)

        elif t == "property_repair":
            houses_cost = p["house"]
            hotel_cost = p["hotel"]
            total = sum(
                (hotel_cost if prop.houses == 5 else prop.houses * houses_cost)
                for prop in player.properties
                if isinstance(prop, PropertySpace) and prop.color not in ["Station", "Utility"]
            )
            self.log(f"{player.name} 支付房产修缮费 ${total}。")
            self._charge_player(player, total, None)

        elif t == "pay_players":
            amount = p["amount"]
            for other in self.active_players():
                if other != player:
                    player.pay_money(amount)
                    other.add_money(amount)
                    self.log(f"{player.name} 向 {other.name} 支付 ${amount}。")

        elif t == "receive_from_players":
            amount = p["amount"]
            for other in self.active_players():
                if other != player:
                    if other.pay_money(amount):
                        player.add_money(amount)
                        self.log(f"{other.name} 给 {player.name} ${ amount}。")

    def _charge_player(self, player, amount, creditor):
        """扣款。不足时尝试清算，再不足则宣告破产。"""
        if player.money >= amount:
            player.money -= amount
            if creditor:
                creditor.add_money(amount)
            return

        net = player.net_worth()
        if net < amount:
            self.log(f"{player.name} 资不抵债！净资产 ${net} < 欠款 ${amount}，宣告破产！")
            self._declare_bankruptcy(player, creditor, amount)
        else:
            self.log(f"{player.name} 现金不足 ${amount - player.money}，需要抵押或卖房。")
            if player.is_ai:
                self._ai_liquidate(player, amount)
                if player.money >= amount:
                    player.money -= amount
                    if creditor:
                        creditor.add_money(amount)
                else:
                    self._declare_bankruptcy(player, creditor, amount)
            else:
                self._force_mortgage(player)
                if player.money >= amount:
                    player.money -= amount
                    if creditor:
                        creditor.add_money(amount)
                else:
                    self._declare_bankruptcy(player, creditor, amount)

    def _declare_bankruptcy(self, player, creditor, debt):
        player.is_bankrupt = True
        self.log(f"{player.name} 宣告破产！")
        for prop in player.properties:
            if creditor:
                prop.owner = creditor
                creditor.properties.append(prop)
                self.log(f"【{prop.name}】转让给 {creditor.name}。")
            else:
                prop.owner = None
                prop.houses = 0
                prop.is_mortgaged = False
                self.log(f"【{prop.name}】归还给银行。")
        if creditor and player.money > 0:
            creditor.add_money(player.money)
        player.money = 0
        player.properties = []
        self.log(f"{player.name} 已淘汰出局。")
        self.next_turn()

    def _force_mortgage(self, player):
        unmortgaged = [
            p for p in player.properties
            if isinstance(p, PropertySpace) and not p.is_mortgaged and p.houses == 0
        ]
        if unmortgaged:
            cheapest = min(unmortgaged, key=lambda p: p.price)
            self.mortgage_property(player, cheapest)

    def _ai_liquidate(self, player, needed):
        """AI 出售房屋并抵押地产来偿还欠款。"""
        for prop in player.properties:
            if isinstance(prop, PropertySpace) and prop.houses > 0 and prop.can_sell_house(self.board):
                while prop.houses > 0 and player.money < needed:
                    sell_price = prop.build_cost // 2
                    if prop.houses == 5:
                        self.bank.hotels += 1
                        prop.houses = 4
                        self.bank.houses -= 4
                    else:
                        self.bank.houses += 1
                        prop.houses -= 1
                    player.add_money(sell_price)
                    self.log(f"AI 出售【{prop.name}】上的房屋，获得 ${sell_price}。")
        for prop in sorted(player.properties, key=lambda p: p.price):
            if player.money >= needed:
                break
            if isinstance(prop, PropertySpace) and not prop.is_mortgaged and prop.houses == 0:
                self.mortgage_property(player, prop)

    # ──────────────────────────── 玩家操作 ───────────────────────────────────

    def buy_property(self, player, space):
        """玩家购买当前所在地块。"""
        if space.owner is not None:
            return False
        if not player.can_afford(space.price):
            self.log(f"{player.name} 资金不足，无法购买（需 ${space.price}）。")
            return False
        player.pay_money(space.price)
        space.owner = player
        player.properties.append(space)
        self.log(f"{player.name} 花费 ${space.price} 购买了【{space.name}】。")
        self.phase = "WAIT_FOR_ROLL"
        if self.doubles_count == 0:
            self.next_turn()
        return True

    def skip_buy(self, player):
        """玩家放弃购买。"""
        self.log(f"{player.name} 放弃购买【{self.board[player.position].name}】。")
        self.phase = "WAIT_FOR_ROLL"
        if self.doubles_count == 0:
            self.next_turn()

    def mortgage_property(self, player, prop):
        if prop.owner != player or prop.is_mortgaged or prop.houses > 0:
            return False
        val = prop.mortgage_value()
        prop.is_mortgaged = True
        player.add_money(val)
        self.log(f"{player.name} 抵押了【{prop.name}】，获得 ${val}。")
        return True

    def unmortgage_property(self, player, prop):
        if prop.owner != player or not prop.is_mortgaged:
            return False
        cost = prop.unmortgage_cost()
        if not player.can_afford(cost):
            self.log(f"{player.name} 资金不足，无法解押【{prop.name}】（需 ${cost}）。")
            return False
        player.pay_money(cost)
        prop.is_mortgaged = False
        self.log(f"{player.name} 解押了【{prop.name}】，支付 ${cost}。")
        return True

    def build_house(self, player, prop):
        if prop.owner != player:
            return False
        if not prop.can_build(self.board):
            self.log(f"无法在【{prop.name}】上建房（需集齐同色或满足均匀建造规则）。")
            return False
        if prop.houses == 4 and self.bank.hotels <= 0:
            self.log("银行旅馆已售罄！")
            return False
        if prop.houses < 4 and self.bank.houses <= 0:
            self.log("银行房屋已售罄！")
            return False
        cost = prop.build_cost
        if not player.can_afford(cost):
            self.log(f"{player.name} 资金不足，无法建房（需 ${cost}）。")
            return False
        player.pay_money(cost)
        if prop.houses == 4:
            self.bank.houses += 4
            self.bank.hotels -= 1
            prop.houses = 5
            self.log(f"{player.name} 在【{prop.name}】上建造了 🏨 旅馆，花费 ${cost}。")
        else:
            self.bank.houses -= 1
            prop.houses += 1
            self.log(f"{player.name} 在【{prop.name}】上建造第 {prop.houses} 栋房屋，花费 ${cost}。")
        return True

    def sell_house(self, player, prop):
        if prop.owner != player or prop.houses == 0:
            return False
        if not prop.can_sell_house(self.board):
            self.log(f"无法出售【{prop.name}】上的房屋（需满足均匀出售规则）。")
            return False
        sell_price = prop.build_cost // 2
        if prop.houses == 5:
            if self.bank.houses < 4:
                self.log("银行房屋库存不足，无法降级旅馆。")
                return False
            self.bank.hotels += 1
            self.bank.houses -= 4
            prop.houses = 4
        else:
            self.bank.houses += 1
            prop.houses -= 1
        player.add_money(sell_price)
        self.log(f"{player.name} 出售了【{prop.name}】上的一栋房屋，获得 ${sell_price}。")
        return True

    # ──────────────────────────── AI 逻辑 ────────────────────────────────────

    def ai_decide_buy(self, player, space):
        if player.can_afford(space.price):
            self.buy_property(player, space)
        else:
            self.log(f"AI {player.name} 资金不足，无法购买【{space.name}】。")
            self.phase = "WAIT_FOR_ROLL"
            if self.doubles_count == 0:
                self.next_turn()

    def ai_build_phase(self, player):
        """AI 尝试在本回合结束后建造房屋。"""
        changed = True
        while changed:
            changed = False
            for prop in sorted(player.properties, key=lambda p: p.price):
                if isinstance(prop, PropertySpace) and prop.can_build(self.board):
                    if player.can_afford(prop.build_cost):
                        self.build_house(player, prop)
                        changed = True

    # ──────────────────────────── 存档 / 读档 ────────────────────────────────

    def to_dict(self):
        """将完整游戏状态序列化为可 JSON 化的字典。"""
        return {
            "version": 1,
            "current_player_index": self.current_player_index,
            "doubles_count": self.doubles_count,
            "last_dice": list(self.last_dice),
            "phase": self.phase,
            "winner": self.winner.name if self.winner else None,
            "bank": self.bank.to_dict(),
            "players": [p.to_dict() for p in self.players],
            "board": [
                s.to_dict() if isinstance(s, PropertySpace) else {"index": s.index}
                for s in self.board
            ],
            "chance_deck_order": [c.to_dict() for c in self.chance_cards],
            "chest_deck_order": [c.to_dict() for c in self.community_chest_cards],
        }

    def save_game(self, filepath):
        """将游戏状态保存到 JSON 文件。"""
        data = self.to_dict()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self.log(f"💾 游戏已保存到 {os.path.basename(filepath)}。")
        return True

    @classmethod
    def load_game(cls, filepath):
        """从 JSON 文件加载游戏状态，返回新的 MonopolyEngine。"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        from board_data import get_board_spaces, get_chance_cards, get_community_chest_cards

        players = [Player.from_dict(pd) for pd in data["players"]]

        engine = cls.__new__(cls)
        engine.board = get_board_spaces()
        engine.logs = []

        player_map = {p.name: p for p in players}
        for space_data in data["board"]:
            idx = space_data["index"]
            space = engine.board[idx]
            if isinstance(space, PropertySpace):
                owner_name = space_data.get("owner_name")
                if owner_name and owner_name in player_map:
                    owner = player_map[owner_name]
                    space.owner = owner
                    owner.properties.append(space)
                space.houses = space_data.get("houses", 0)
                space.is_mortgaged = space_data.get("is_mortgaged", False)

        all_chance = {c.id_str: c for c in get_chance_cards()}
        all_chest = {c.id_str: c for c in get_community_chest_cards()}
        engine.chance_cards = [all_chance[d["id_str"]] for d in data["chance_deck_order"] if d["id_str"] in all_chance]
        engine.community_chest_cards = [all_chest[d["id_str"]] for d in data["chest_deck_order"] if d["id_str"] in all_chest]
        engine.chance_discard = []
        engine.chest_discard = []

        engine.players = players
        engine.current_player_index = data["current_player_index"]
        engine.doubles_count = data["doubles_count"]
        engine.last_dice = tuple(data["last_dice"])
        engine.phase = data["phase"]
        engine.bank = Bank()
        engine.bank.from_dict(data["bank"])

        winner_name = data.get("winner")
        engine.winner = player_map.get(winner_name) if winner_name else None

        engine.logs.append("📂 游戏加载成功。")
        return engine
