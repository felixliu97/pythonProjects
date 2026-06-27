"""
体育博彩跨平台套利计算器
===========================
读取 JSON 文件中多个平台的赔率数据，计算是否存在套利空间。
支持二项盘（胜/负）和三项盘（胜/平/负）。

套利原理：
  对于每个结果（outcome），选取所有平台中最高的赔率。
  如果 Σ(1 / best_odds_i) < 1，则存在套利空间。
  套利利润率 = (1 - Σ(1 / best_odds_i)) / Σ(1 / best_odds_i) × 100%
"""

import json
import sys
from pathlib import Path
import datetime

# Windows 终端 UTF-8 输出兼容
sys.stdout.reconfigure(encoding="utf-8")
from typing import Any


# ─── 颜色输出 ───────────────────────────────────────────────────────
class Colors:
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    DIM = "\033[2m"
    RESET = "\033[0m"


# ─── 核心计算 ───────────────────────────────────────────────────────
OUTCOME_LABELS = {
    "3way": {"win": "主胜", "draw": "平局", "lose": "客胜"},
    "2way": {"win": "主胜", "lose": "客胜"},
}


def find_best_odds(
    platforms: dict[str, dict[str, float]], outcomes: list[str]
) -> dict[str, tuple[float, str]]:
    """
    对每个结果找出所有平台中的最高赔率。
    返回 {outcome: (best_odds, platform_name)}
    """
    best = {}
    for outcome in outcomes:
        best_odds = -1.0
        best_platform = ""
        for platform, odds in platforms.items():
            if outcome in odds and odds[outcome] > best_odds:
                best_odds = odds[outcome]
                best_platform = platform
        best[outcome] = (best_odds, best_platform)
    return best


def calculate_arbitrage(
    best_odds: dict[str, tuple[float, str]],
) -> tuple[bool, float, float]:
    """
    计算套利空间。
    返回 (is_arbitrage, margin_sum, profit_pct)
      - margin_sum: 各最佳赔率倒数之和（< 1 = 有套利）
      - profit_pct: 套利利润率 (%)
    """
    margin_sum = sum(1.0 / odds for odds, _ in best_odds.values())
    is_arb = margin_sum < 1.0
    profit_pct = ((1.0 / margin_sum) - 1.0) * 100.0 if is_arb else 0.0
    return is_arb, margin_sum, profit_pct


def calculate_stakes(
    best_odds: dict[str, tuple[float, str]], total_stake: float
) -> dict[str, dict[str, Any]]:
    """
    给定总投注金额，计算每个结果的最优分配。
    无论哪个结果发生，收益相同（= total_stake / margin_sum）。
    """
    margin_sum = sum(1.0 / odds for odds, _ in best_odds.values())
    guaranteed_return = total_stake / margin_sum
    stakes = {}
    for outcome, (odds, platform) in best_odds.items():
        stake = total_stake / (odds * margin_sum)
        profit = guaranteed_return - total_stake
        stakes[outcome] = {
            "platform": platform,
            "odds": odds,
            "stake": round(stake, 2),
            "payout": round(stake * odds, 2),
            "profit": round(profit, 2),
        }
    return stakes


# ─── 单场比赛简要格式化 ────────────────────────────────────────────────
def format_best_odds_str(best_odds: dict[str, tuple[float, str]], market_type: str) -> str:
    """格式化最佳赔率组合在一行中展示。"""
    labels = OUTCOME_LABELS.get(market_type, OUTCOME_LABELS["3way"])
    parts = []
    for oc, (odds, plat) in best_odds.items():
        # 简写 outcome
        short_label = labels[oc][0]  # "主", "平", "客"
        parts.append(f"{short_label}:{odds:.2f}({plat})")
    return " / ".join(parts)


# ─── 单场比赛分析 ───────────────────────────────────────────────────
def analyze_match(match: dict, total_stake: float = 1000.0) -> bool:
    """分析单场比赛的套利机会，返回是否存在套利。"""
    name = match["name"]
    market_type = match.get("type", "3way")
    platforms = match["platforms"]
    outcomes = list(OUTCOME_LABELS.get(market_type, OUTCOME_LABELS["3way"]).keys())
    labels = OUTCOME_LABELS.get(market_type, OUTCOME_LABELS["3way"])

    # 标题
    print(f"\n{'═' * 70}")
    print(f"  {Colors.BOLD}{Colors.CYAN}⚽ {name}{Colors.RESET}")
    if "match_time" in match and match["match_time"] != "-":
        print(f"  {Colors.DIM}比赛时间: {match['match_time']}{Colors.RESET}")
    print(
        f"  {Colors.DIM}盘口类型: {'三项盘（胜/平/负）' if market_type == '3way' else '二项盘（胜/负）'}{Colors.RESET}"
    )
    print(f"{'═' * 70}")

    # 各平台赔率表
    header = f"  {'平台':<22}"
    for oc in outcomes:
        header += f"  {labels[oc]:>6}"
    print(header)
    print(f"  {'─' * 60}")

    for platform, odds in platforms.items():
        time_suffix = ""
        if "updated_at" in odds:
            # show HH:MM format e.g. (19:00)
            time_suffix = f" ({odds['updated_at'][11:16]})"
        row = f"  {platform + time_suffix:<22}"
        for oc in outcomes:
            row += f"  {odds.get(oc, '-'):>6}"
        print(row)

    # 最佳赔率
    best = find_best_odds(platforms, outcomes)
    print(f"\n  {Colors.BOLD}📊 最佳赔率组合:{Colors.RESET}")
    for oc in outcomes:
        odds, plat = best[oc]
        print(f"     {labels[oc]}: {Colors.YELLOW}{odds:.2f}{Colors.RESET} ← {plat}")

    # 套利判断
    is_arb, margin_sum, profit_pct = calculate_arbitrage(best)

    print(f"\n  综合隐含概率: {margin_sum:.4f} ", end="")
    if is_arb:
        print(f"{Colors.GREEN}(< 1.0 ✅ 存在套利空间!){Colors.RESET}")
        print(
            f"  {Colors.GREEN}{Colors.BOLD}💰 套利利润率: {profit_pct:.2f}%{Colors.RESET}"
        )

        # 投注分配
        stakes = calculate_stakes(best, total_stake)
        print(
            f"\n  {Colors.BOLD}📋 最优投注分配 (总投注: ${total_stake:,.2f}):{Colors.RESET}"
        )
        print(f"  {'─' * 60}")
        print(
            f"  {'结果':<8} {'平台':<14} {'赔率':>6} {'投注额':>10} {'赔付':>10} {'利润':>10}"
        )
        print(f"  {'─' * 60}")
        for oc in outcomes:
            s = stakes[oc]
            print(
                f"  {labels[oc]:<8} {s['platform']:<14} {s['odds']:>6.2f} "
                f"${s['stake']:>9,.2f} ${s['payout']:>9,.2f} "
                f"{Colors.GREEN}${s['profit']:>9,.2f}{Colors.RESET}"
            )
        print(f"  {'─' * 60}")
        guaranteed = list(stakes.values())[0]["payout"]
        print(
            f"  {Colors.GREEN}{Colors.BOLD}  无论结果如何，保证收益: ${guaranteed:,.2f} "
            f"(净利润 ${guaranteed - total_stake:,.2f}){Colors.RESET}"
        )
    else:
        overround = (margin_sum - 1.0) * 100.0
        print(f"{Colors.RED}(≥ 1.0 ❌ 无套利空间){Colors.RESET}")
        print(
            f"  {Colors.RED}庄家综合抽水: {overround:.2f}%{Colors.RESET}"
        )

    return is_arb


# ─── 时间解析与排序 ──────────────────────────────────────────────────
def parse_match_time(time_str: str) -> datetime.datetime:
    """解析比赛时间（如 'Fri 19 Jun 19:41'）为 sortable datetime 对象"""
    if not time_str or time_str == "-":
        return datetime.datetime.max
    try:
        # 假设年份为当前本地年份
        current_year = datetime.datetime.now().year
        # 处理可能的月份简写和星期简写
        return datetime.datetime.strptime(f"{current_year} {time_str}", "%Y %a %d %b %H:%M")
    except Exception:
        return datetime.datetime.max


# ─── 主程序 ─────────────────────────────────────────────────────────
def main():
    # 默认 JSON 文件路径
    json_path = Path(__file__).parent / "odds_data.json"
    if len(sys.argv) > 1:
        json_path = Path(sys.argv[1])

    total_stake = 1000.0
    if len(sys.argv) > 2:
        total_stake = float(sys.argv[2])

    if not json_path.exists():
        print(f"{Colors.RED}错误: 找不到文件 {json_path}{Colors.RESET}")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    matches = data.get("matches", [])
    if not matches:
        print(f"{Colors.RED}错误: JSON 中没有找到比赛数据{Colors.RESET}")
        sys.exit(1)

    # 预先计算所有比赛的套利指标以供排序
    processed_matches = []
    for match in matches:
        market_type = match.get("type", "3way")
        outcomes = list(OUTCOME_LABELS.get(market_type, OUTCOME_LABELS["3way"]).keys())
        best = find_best_odds(match["platforms"], outcomes)
        is_arb, margin_sum, profit_pct = calculate_arbitrage(best)
        processed_matches.append({
            "match": match,
            "best": best,
            "is_arb": is_arb,
            "margin_sum": margin_sum,
            "profit_pct": profit_pct,
            "market_type": market_type
        })

    # 按开赛时间升序排序 (最早开赛的排在最前面)
    processed_matches.sort(key=lambda x: parse_match_time(x["match"].get("match_time", "-")))

    # 打印简要汇总表格
    print(f"\n{Colors.BOLD}{'=' * 95}")
    print(f"  🎯 体育博彩跨平台套利计算器")
    print(f"  📁 数据文件: {json_path.name} | 💵 模拟总投注额: ${total_stake:,.2f} | 📊 比赛数量: {len(matches)}")
    print(f"{'=' * 95}{Colors.RESET}")
    
    print(f"\n  {Colors.BOLD}📋 赛事盘口分析列表 (按开赛时间顺序排序):{Colors.RESET}")

    print(f"  {'─' * 95}")
    print(f"  {'序号':<4} {'比赛/对手':<28} {'类型':<4} {'综合概率':>8} {'状态/收益':>12}  {'最佳赔率组合':<32}")
    print(f"  {'─' * 95}")
    
    arb_count = 0
    for idx, pm in enumerate(processed_matches, 1):
        m = pm["match"]
        name_truncated = m["name"][:26] + "..." if len(m["name"]) > 26 else m["name"]
        
        # 状态/收益展示
        if pm["is_arb"]:
            status_str = f"{Colors.GREEN}+{pm['profit_pct']:.2f}% ✅{Colors.RESET}"
            arb_count += 1
        else:
            loss_pct = (pm["margin_sum"] - 1.0) * 100.0
            status_str = f"{Colors.RED}-{loss_pct:.2f}% ❌{Colors.RESET}"
            
        best_odds_str = format_best_odds_str(pm["best"], pm["market_type"])
        
        print(f"  {idx:<4} {name_truncated:<28} {pm['market_type']:<4} {pm['margin_sum']:>8.4f} {status_str:>20}  {best_odds_str}")
    print(f"  {'─' * 95}")

    # 打印详细分析
    print(f"\n\n{Colors.BOLD}🔍 详细赔率分配与分析 (按潜力排序):{Colors.RESET}")
    for pm in processed_matches:
        analyze_match(pm["match"], total_stake)

    # 汇总
    print(f"\n{'═' * 70}")
    print(f"  {Colors.BOLD}📊 汇总报告{Colors.RESET}")
    print(f"{'═' * 70}")
    print(f"  分析比赛: {len(matches)} 场")
    if arb_count > 0:
        print(
            f"  {Colors.GREEN}{Colors.BOLD}发现套利机会: {arb_count} 场 ✅{Colors.RESET}"
        )
    else:
        print(
            f"  {Colors.RED}发现套利机会: 0 场 — 当前无套利空间{Colors.RESET}"
        )
    print()

    # 导出至 Markdown 文件
    report_path = json_path.parent / "arbitrage_report.md"
    generate_markdown_report(processed_matches, total_stake, json_path.name, report_path)
    print(f"  {Colors.GREEN}📝 套利分析报告已导出至: {report_path.name}{Colors.RESET}\n")


def generate_markdown_report(processed_matches, total_stake, json_name, report_path):
    import datetime
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    md = []
    md.append("# 🎯 体育博彩跨平台套利分析报告")
    md.append(f"- **生成时间**: `{now_str}`")
    md.append(f"- **数据文件**: `{json_name}`")
    md.append(f"- **模拟总投注额**: `${total_stake:,.2f}`")
    md.append(f"- **分析比赛数量**: {len(processed_matches)} 场")
    
    # 汇总
    arb_count = sum(1 for pm in processed_matches if pm["is_arb"])
    if arb_count > 0:
        md.append(f"\n### 📊 汇总: **发现 {arb_count} 场套利机会！✅**")
    else:
        md.append("\n### 📊 汇总: **未发现任何套利机会。❌**")
        
    md.append("\n## 📋 赛事盘口分析列表 (按开赛时间顺序排序)")
    md.append("| 序号 | 比赛/对手 | 比赛时间 | 类型 | 综合隐含概率 | 状态/收益 | 最佳赔率组合 |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

    
    for idx, pm in enumerate(processed_matches, 1):
        m = pm["match"]
        if pm["is_arb"]:
            status_str = f"**+{pm['profit_pct']:.2f}% ✅**"
        else:
            loss_pct = (pm["margin_sum"] - 1.0) * 100.0
            status_str = f"-{loss_pct:.2f}% ❌"
            
        labels = OUTCOME_LABELS.get(pm["market_type"], OUTCOME_LABELS["3way"])
        odds_parts = []
        for oc, (odds, plat) in pm["best"].items():
            short_label = labels[oc][0]
            odds_parts.append(f"{short_label}:{odds:.2f}({plat})")
        best_odds_str = " / ".join(odds_parts)
        
        match_time = m.get("match_time", "-")
        md.append(f"| {idx} | {m['name']} | {match_time} | {pm['market_type']} | {pm['margin_sum']:.4f} | {status_str} | {best_odds_str} |")
        
    md.append("\n## 🔍 详细赔率分配与分析")
    for idx, pm in enumerate(processed_matches, 1):
        m = pm["match"]
        market_type = pm["market_type"]
        platforms = m["platforms"]
        outcomes = list(OUTCOME_LABELS.get(market_type, OUTCOME_LABELS["3way"]).keys())
        labels = OUTCOME_LABELS.get(market_type, OUTCOME_LABELS["3way"])
        
        md.append(f"\n### {idx}. {m['name']}")
        if "match_time" in m and m["match_time"] != "-":
            md.append(f"- **比赛时间**: {m['match_time']}")
        md.append(f"- **盘口类型**: {'三项盘（胜/平/负）' if market_type == '3way' else '二项盘（胜/负）'}")
        
        # Odds table
        headers = ["平台 (更新时间)"] + [labels[oc] for oc in outcomes]
        md.append("| " + " | ".join(headers) + " |")
        md.append("| " + " | ".join([":---"] * len(headers)) + " |")
        for plat, odds in platforms.items():
            time_str = f" ({odds['updated_at']})" if "updated_at" in odds else ""
            row = [plat + time_str] + [str(odds.get(oc, "-")) for oc in outcomes]
            md.append("| " + " | ".join(row) + " |")
            
        md.append("\n**最佳赔率组合**:")
        for oc in outcomes:
            odds, plat = pm["best"][oc]
            md.append(f"- {labels[oc]}: `{odds:.2f}` ← {plat}")
            
        if pm["is_arb"]:
            md.append(f"\n> 💰 **套利利润率: {pm['profit_pct']:.2f}%**")
            # Stake distribution
            stakes = calculate_stakes(pm["best"], total_stake)
            md.append("\n| 结果 | 平台 | 赔率 | 最佳投注额 | 保证赔付 | 净利润 |")
            md.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
            for oc in outcomes:
                s = stakes[oc]
                md.append(f"| {labels[oc]} | {s['platform']} | {s['odds']:.2f} | `${s['stake']:,.2f}` | `${s['payout']:,.2f}` | `${s['profit']:,.2f}` |")
            guaranteed = list(stakes.values())[0]["payout"]
            md.append(f"\n**无论结果如何，保证收益: `${guaranteed:,.2f}` (净利润 `${guaranteed - total_stake:,.2f}`)**\n")
        else:
            overround = (pm["margin_sum"] - 1.0) * 100.0
            md.append(f"\n> ❌ **无套利空间 (庄家抽水: {overround:.2f}%)**\n")
            
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))


if __name__ == "__main__":
    main()

