"""AI World Cup Gambler.

Single-file virtual betting simulator for AI agents.

Public API:
    cmd(command_string: str) -> str
"""

from __future__ import annotations

import json
import math
import os
import re
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


SAVE_FILE = Path(__file__).with_name("gambler_save.json")
MIN_BET = 100
STARTING_CASH = 100_000
LOAN_AMOUNT = 50_000
LOAN_RATE = 0.10
DEBT_LIMIT = 500_000
QUERY_COMMANDS = {"schedule", "status", "news", "history", "summary", "standings", "titles"}


OPENING_TEXT = """⚽ 赌狗的自我修养 · AI 世界杯赌球模拟器

你是一个赌球爱好者。10 万块起步，16 支球队，虚拟世界杯。
看赔率、读新闻、押比分、赌大小——然后看着余额一点点消失。

输光了？没关系，高利贷等着你。
不借？那就 Game Over。

目标很简单：别亏光。
但你知道的，赌狗的目标从来不是「别亏光」，而是「再来一把」。

免责声明：这是虚拟游戏，不涉及真实金钱，不提供任何现实赌博建议。"""


TEAMS: List[Dict[str, Any]] = [
    {"id": "brazilia", "name": "Brazilia", "power": 92, "tier": 1},
    {"id": "argentino", "name": "Argentino", "power": 90, "tier": 1},
    {"id": "franch", "name": "Franch", "power": 89, "tier": 1},
    {"id": "germeny", "name": "Germeny", "power": 87, "tier": 1},
    {"id": "espanya", "name": "Espanya", "power": 85, "tier": 2},
    {"id": "englund", "name": "Englund", "power": 84, "tier": 2},
    {"id": "portugalo", "name": "Portugalo", "power": 83, "tier": 2},
    {"id": "belgica", "name": "Belgica", "power": 82, "tier": 2},
    {"id": "nederlund", "name": "Nederlund", "power": 80, "tier": 3},
    {"id": "kroatia", "name": "Kroatia", "power": 79, "tier": 3},
    {"id": "uruguayo", "name": "Uruguayo", "power": 78, "tier": 3},
    {"id": "italio", "name": "Italio", "power": 77, "tier": 3},
    {"id": "japon", "name": "Japón", "power": 74, "tier": 4},
    {"id": "koreo", "name": "Koreo", "power": 73, "tier": 4},
    {"id": "mexica", "name": "Mexica", "power": 72, "tier": 4},
    {"id": "merican", "name": "Merican", "power": 71, "tier": 4},
]

TEAM_BY_ID = {team["id"]: team for team in TEAMS}
GROUPS = ["A", "B", "C", "D"]
GROUP_PAIRINGS = [
    [(0, 1), (2, 3)],
    [(0, 2), (1, 3)],
    [(0, 3), (1, 2)],
]

KNOCKOUT_INFO = {
    12: ("qf", "8强赛", "八强开门，输的人可以提前研究机票。"),
    13: ("four", "半决赛", "离奖杯越近，离天台也可能越近。"),
    14: ("placement", "5-8名排位赛", "八强输家也要继续踢，毕竟机票不能改签太早。"),
    15: ("third", "三四名决赛", "铜牌也是牌，别笑，至少人家没梭哈输光。"),
    16: ("final", "决赛", "最后一场。庄家已经把香槟冰好了。"),
}

TITLE_NAMES = {
    "analyst": "📊 民间分析师",
    "steady": "🏦 稳健理财",
    "tuition": "📚 交学费中",
    "hupu_bro": "🏀 虎扑老哥",
    "rooftop": "🏢 天台观光客",
    "loan_vip": "💳 高利贷 VIP",
    "dog_end": "🐕 赌狗末路",
    "paul": "🐙 章鱼保罗转世",
    "emperor": "👑 欧皇降临",
    "reverse": "🏖️ 反买别墅靠海",
    "yolo": "🎰 一把梭的代价",
    "hopeless": "💀 这辈子就这样了",
    "beginner_luck": "🍀 新手保护期",
    "chaser": "🔥 追加投注者",
    "conservative": "🐢 保守派",
    "all_correct_group": "🔮 小组赛全知",
    "champion_predict": "🏆 冠军预言家",
}

TITLE_TAUNTS = {
    "paul": "你是预言家还是单纯运气好？先别膨胀。",
    "emperor": "串关都能中，今天空气里有玄学味。",
    "reverse": "大家已经开始抄你的反向作业了。",
    "yolo": "All in 的结局通常只有一种，你亲自演示了一遍。",
    "hopeless": "高利贷都救不了你，庄家都沉默了。",
    "beginner_luck": "第一把就赢，最危险的幻觉已经到账。",
    "chaser": "「翻本」两个字，听起来就很贵。",
    "conservative": "连续小注，像在给庄家交手续费分期付款。",
    "all_correct_group": "小组赛你看穿了，人生怎么没顺便看穿？",
    "champion_predict": "冠军都猜中了，你确定不是庄家实习生？",
}

BET_CONFIRMATIONS = [
    "庄家翻开账本，给你留了个微笑。",
    "下注已存档。理性在门口等你，暂时没进来。",
    "票据打印完成，命运开始装作很忙。",
    "市场接单成功。你听见余额轻轻叹气。",
    "下注确认。接下来请把玄学说得更坚定一点。",
    "庄家收单，空气里有一点不祥的礼貌。",
]

NEWS = {
    "positive": [
        ("⚽", "{team} 主力前锋伤愈复出，球队士气大振。"),
        ("⚽", "{team} 近 5 场比赛保持不败，状态火热。"),
        ("⚽", "{team} 主教练赛前放话：「这场必须拿下。」"),
        ("📊", "数据分析师预测 {team} 本场胜率高达 75%。"),
    ],
    "negative": [
        ("🏥", "{team} 核心球员赛前训练受伤，出场成疑。"),
        ("😴", "{team} 昨晚抵达赛场，疑似受时差影响。"),
        ("💔", "{team} 更衣室不和传闻甚嚣尘上。"),
        ("📉", "博彩公司大幅下调 {team} 胜率，原因不明。"),
    ],
    "misleading": [
        ("🔮", "玄学分析：{team} 球衣颜色与冠军色高度吻合。"),
        ("🐙", "章鱼哥预测 {team} 将在本场取胜。"),
        ("📱", "社交媒体热议：{team} 球员赛前集体发鸡汤，不祥之兆？"),
        ("🎰", "某神秘大户重注押 {team} 赢，投注额破纪录。"),
    ],
    "match_event": [
        ("🌧️", "本场比赛遭遇暴雨，场地湿滑可能影响发挥。"),
        ("🏟️", "本场比赛上座率创纪录，主队优势明显。"),
        ("🟥", "裁判以严厉执法著称，本场红牌概率较高。"),
    ],
}

NEWS_SOURCES = [
    "球场耳语",
    "数据黑箱",
    "更衣室电台",
    "盘口观察站",
]

MOODS = {
    "big_win": [
        "🤑 赢麻了！你开始幻想靠虚拟赌球实现虚拟财务自由。",
        "🚀 连赢之后你觉得自己掌握了足球的规律。庄家听了都想鼓掌。",
        "👑 朋友都来问你要分析，你假装谦虚，其实已经飘到看不见地面。",
    ],
    "small_win": [
        "😊 小赚一笔，但你总觉得本来可以下更多。危险想法已上线。",
        "💭 「早知道就多押点了……」这句话通常是亏钱的序章。",
    ],
    "small_loss": [
        "😐 亏了一点，不痛不痒。你告诉自己下把赢回来。",
        "🤔 「这个赔率明明很稳啊……」庄家最爱听这种话。",
    ],
    "big_loss": [
        "😰 一把亏掉一截本金。你开始怀疑人生，也开始怀疑裁判。",
        "💸 你盯着余额看了很久，然后决定继续嘴硬。",
        "🕳️ 「再来一把，我感觉下一场肯定稳。」这句话已经开始收利息了。",
    ],
    "broke": [
        "💀 余额：0。你的虚拟赌球生涯走到了岔路口。",
        "🏢 天台风很大。要借高利贷翻本吗？（loan / quit）",
    ],
    "in_debt": [
        "📉 负债累累，利息还在涨。你只是换了一种方式给庄家打工。",
        "🐕 赌狗的尽头不是翻本，是更大的坑。",
    ],
}


class RNG:
    """Small deterministic PRNG based on mulberry32."""

    def __init__(self, state: int):
        self.state = state & 0xFFFFFFFF

    def random(self) -> float:
        self.state = (self.state + 0x6D2B79F5) & 0xFFFFFFFF
        t = self.state
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t ^= (t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0

    def randint(self, low: int, high: int) -> int:
        return low + int(self.random() * (high - low + 1))

    def choice(self, items: List[Any]) -> Any:
        return items[self.randint(0, len(items) - 1)]

    def shuffle(self, items: List[Any]) -> None:
        for i in range(len(items) - 1, 0, -1):
            j = self.randint(0, i)
            items[i], items[j] = items[j], items[i]

    def uniform(self, low: float, high: float) -> float:
        return low + (high - low) * self.random()


def cmd(command_string: str) -> str:
    """唯一交互入口：接受纯文本命令，返回纯文本结果。"""
    command_string = (command_string or "").strip()
    if not command_string:
        return "请输入命令。试试：help"

    parts = command_string.split()
    command = parts[0].lower()
    json_mode = command in QUERY_COMMANDS and len(parts) > 1 and parts[-1] == "--json"
    if json_mode:
        parts = parts[:-1]

    try:
        if command == "help":
            return _help_text()
        if command == "new_game":
            return _cmd_new_game(parts)

        state = _load_state()
        if not state:
            return "还没开局。先输入：new_game 12345"

        if command == "status":
            return _json_response(_status_data(state)) if json_mode else _cmd_status(state)
        if command == "schedule":
            return _json_response(_schedule_data(state)) if json_mode else _cmd_schedule(state)
        if command == "standings":
            return _json_response(_standings_data(state)) if json_mode else _cmd_standings(state)
        if command == "bet":
            text = _cmd_bet(state, parts)
            _save_state(state)
            return text
        if command == "parlay":
            text = _cmd_parlay(state, parts)
            _save_state(state)
            return text
        if command == "next":
            text = _cmd_next(state)
            _save_state(state)
            return text
        if command == "history":
            return _json_response(_history_data(state)) if json_mode else _cmd_history(state)
        if command == "summary":
            return _json_response(_summary_data(state)) if json_mode else _cmd_summary(state)
        if command == "titles":
            return _json_response(_titles_data(state)) if json_mode else _cmd_titles(state)
        if command == "news":
            return _json_response(_news_data(state)) if json_mode else _cmd_news(state)
        if command == "loan":
            text = _cmd_loan(state)
            _save_state(state)
            return text
        if command == "repay":
            text = _cmd_repay(state, parts)
            _save_state(state)
            return text
        if command == "quit":
            text = _cmd_quit(state)
            _save_state(state)
            return text

        return f"未知命令：{command}。试试：help"
    except Exception as exc:  # Keeps the pure text API friendly for agents.
        if os.environ.get("GAMBLER_DEBUG") == "1":
            return (
                f"\u547d\u4ee4\u6267\u884c\u5931\u8d25\uff1a{exc}\n"
                f"{traceback.format_exc()}"
                "\u8fd9\u4e0d\u662f\u7384\u5b66\uff0c\u662f\u4ee3\u7801\u5728\u54b3\u55fd\u3002"
                "\u8bf7\u68c0\u67e5\u547d\u4ee4\u683c\u5f0f\u3002"
            )
        return f"命令执行失败：{exc}\n这不是玄学，是代码在咳嗽。请检查命令格式。"


def _cmd_new_game(parts: List[str]) -> str:
    if len(parts) != 2:
        return "用法：new_game <seed>，例如：new_game 12345"
    seed = _parse_seed(parts[1])
    state = _new_state(seed)
    _save_state(state)
    return "\n\n".join(
        [
            OPENING_TEXT,
            f"新游戏已开始。Seed = {seed}",
            _format_groups(state),
            _cmd_status(state),
            "输入 schedule 查看本轮比赛，输入 news 阅读本轮传闻。友情提示：传闻不负责赔钱。",
        ]
    )


def _cmd_status(state: Dict[str, Any]) -> str:
    _refresh_dynamic_titles(state)
    settled = [bet for bet in state["bets"] if bet["settled"]]
    wins = sum(1 for bet in settled if bet["won"])
    win_rate = (wins / len(settled) * 100) if settled else 0.0
    pending = sum(1 for bet in state["bets"] if not bet["settled"])
    net = _net_assets(state)
    round_name = _round_name(state)
    dynamic = TITLE_NAMES.get(state.get("dynamic_title", "steady"), "🏦 稳健理财")
    permanent = [TITLE_NAMES[t] for t in state["permanent_titles"]]
    title_line = dynamic
    if permanent:
        title_line += " | " + "、".join(permanent[-4:])
    ended = "是" if state.get("ended") else "否"
    lines = [
        "📒 状态面板",
        f"现金：{state['cash']:,}",
        f"债务：{state['debt']:,}",
        f"净资产：{net:,}",
        f"当前轮次：{state['round_index'] + 1 if not state.get('ended') else '-'} / 17",
        f"阶段：{round_name}",
        f"称号：{title_line}",
        f"累计盈亏：{state['total_profit']:+,}",
        f"下注胜率：{win_rate:.1f}% ({wins}/{len(settled)})",
        f"已下注次数：{len(state['bets'])}，待结算：{pending}",
        f"最大单笔盈利：{state['max_single_win']:+,}",
        f"最大单笔亏损：{state['max_single_loss']:+,}",
        f"游戏结束：{ended}",
    ]
    if state["cash"] < MIN_BET and not state.get("ended"):
        lines.append("余额低于最低下注。现在可以 loan 借高利贷，或 quit 体面退场。")
    return "\n".join(lines)


def _cmd_schedule(state: Dict[str, Any]) -> str:
    if state.get("ended"):
        return "游戏已经结束。庄家把账本合上了。"
    matches = state.get("current_matches", [])
    if not matches:
        return "当前没有可下注比赛。可能奖杯已经颁完了。"
    lines = [
        f"🗓️ 当前赛程：第 {state['round_index'] + 1} / 17 轮 · {_round_name(state)}",
        "下注编号只在当前轮有效。赔率已经抽水，别幻想长期正期望。",
    ]
    for index, match in enumerate(matches, 1):
        home = _team_name(match["home"])
        away = _team_name(match["away"])
        wnl = match["odds"]["wnl"]
        goals = match["odds"]["goals"]
        examples = match["odds"]["score_examples"]
        lines.append("")
        lines.append(f"[{index}] {home} vs {away} | {match['stage_label']}")
        lines.append(
            "  胜平负："
            f"home {wnl['home']:.2f} / draw {wnl['draw']:.2f} / away {wnl['away']:.2f}"
        )
        lines.append(
            "  总进球："
            f"over2 {goals['over2']:.2f} / under3 {goals['under3']:.2f} / "
            f"over3 {goals['over3']:.2f} / under4 {goals['under4']:.2f}"
        )
        lines.append(
            "  比分示例："
            + " / ".join(f"{score} {odd:.2f}" for score, odd in examples.items())
        )
        if match["stage"] != "group":
            pk = match["odds"]["pk"]
            lines.append(f"  点球大战：yes {pk['yes']:.2f} / no {pk['no']:.2f}")
            lines.append("  注：胜平负是 90 分钟赛果；晋级会通过加时/点球产生。")
    return "\n".join(lines)


def _cmd_standings(state: Dict[str, Any]) -> str:
    if state["round_index"] < 12 and not state.get("ended"):
        lines = ["📊 小组积分榜"]
        for group in GROUPS:
            lines.append("")
            lines.append(f"Group {group}")
            lines.append("队伍          赛  分  胜  平  负  进  失  净")
            for team_id in _sorted_group(state, group):
                row = state["standings"][group][team_id]
                lines.append(
                    f"{_team_name(team_id):<12} {row['played']:>2} {row['pts']:>3} "
                    f"{row['w']:>2} {row['d']:>2} {row['l']:>2} "
                    f"{row['gf']:>3} {row['ga']:>3} {row['gd']:>3}"
                )
        return "\n".join(lines)

    lines = ["🏆 淘汰赛对阵与晋级"]
    bracket = state.get("bracket") or {}
    if bracket.get("qualified"):
        lines.append("出线队：" + "、".join(_team_name(t) for t in bracket["qualified"]))
    knockout_matches = [m for m in state["all_matches"] if m["stage"] != "group"]
    if knockout_matches:
        lines.append("")
        lines.append("已赛：")
        for match in knockout_matches[-10:]:
            lines.append("  " + _format_match_result(match))
    current = state.get("current_matches", [])
    if current:
        lines.append("")
        lines.append("当前待赛：")
        for index, match in enumerate(current, 1):
            lines.append(
                f"  [{index}] {_team_name(match['home'])} vs {_team_name(match['away'])} "
                f"({match['stage_label']})"
            )
    if bracket.get("champion"):
        lines.append("")
        lines.append(f"冠军：{_team_name(bracket['champion'])}")
        lines.append(f"亚军：{_team_name(bracket.get('runner_up'))}")
        lines.append(f"季军：{_team_name(bracket.get('third'))}")
    return "\n".join(lines)


def _cmd_bet(state: Dict[str, Any], parts: List[str]) -> str:
    if state.get("ended"):
        return "游戏已经结束，不能再下注。庄家拒绝售后。"
    if len(parts) != 5:
        return "用法：bet <wnl/score/goals/pk> <match_index> <pick> <amount>"
    kind = parts[1].lower()
    match = _match_by_display_index(state, parts[2])
    if not match:
        return "比赛编号无效。输入 schedule 查看当前轮可下注比赛。"
    amount = _parse_amount(parts[-1])
    if isinstance(amount, str):
        return amount
    if state["cash"] < amount:
        return f"资金不足。当前现金 {state['cash']:,}，下注 {amount:,}。庄家不接受画饼。"

    pick = parts[3].lower()
    if kind == "wnl":
        if pick not in {"home", "draw", "away"}:
            return "胜平负 pick 必须是 home / draw / away。"
        odds = match["odds"]["wnl"][pick]
        fair_odds = _fair_odds(match["probs"][pick])
        description = f"{_team_name(match['home'])} vs {_team_name(match['away'])} · {pick}"
    elif kind == "score":
        if not re.match(r"^\d{1,2}-\d{1,2}$", pick):
            return "比分格式错误。示例：bet score 1 2-1 1000"
        home_goals, away_goals = [int(x) for x in pick.split("-")]
        if home_goals > 9 or away_goals > 9:
            return "比分别太离谱，0-9 之间就够庄家笑了。"
        odds = _score_odds(match, home_goals, away_goals)
        fair_odds = _fair_odds(_score_probability(match, home_goals, away_goals))
        description = f"{_team_name(match['home'])} vs {_team_name(match['away'])} · {pick}"
    elif kind == "goals":
        parsed = _parse_goals_pick(pick)
        if not parsed:
            return "总进球 pick 格式错误。示例：over3 / under3 / over2 / under4"
        odds = match["odds"]["goals"].get(pick)
        if odds is None:
            mode, line = parsed
            odds = _goals_odds(match, mode, line)
        mode, line = parsed
        fair_odds = _fair_odds(_goals_probability(match, mode, line))
        description = f"{_team_name(match['home'])} vs {_team_name(match['away'])} · {pick}"
    elif kind == "pk":
        if match["stage"] == "group":
            return "点球大战玩法仅限淘汰赛。小组赛点球？裁判听了都摇头。"
        if pick not in {"yes", "no"}:
            return "点球大战 pick 必须是 yes / no。"
        odds = match["odds"]["pk"][pick]
        pk_prob_yes = match["probs"]["draw"] * 0.50
        fair_odds = _fair_odds(pk_prob_yes if pick == "yes" else max(0.001, 1 - pk_prob_yes))
        description = f"{_team_name(match['home'])} vs {_team_name(match['away'])} · PK {pick}"
    else:
        return "未知玩法。支持：wnl / score / goals / pk"

    return _place_bet(state, kind, amount, odds, fair_odds, description, match, pick)


def _cmd_parlay(state: Dict[str, Any], parts: List[str]) -> str:
    if state.get("ended"):
        return "游戏已经结束，串关也救不了。"
    if len(parts) != 4:
        return "用法：parlay 1,2,3 home,away,home 3000"
    indexes = [item.strip() for item in parts[1].split(",") if item.strip()]
    picks = [item.strip().lower() for item in parts[2].split(",") if item.strip()]
    if len(indexes) < 2:
        return "串关至少需要 2 场。单场那叫普通嘴硬。"
    if len(indexes) != len(picks):
        return "比赛编号数量和 picks 数量不一致。"
    amount = _parse_amount(parts[3])
    if isinstance(amount, str):
        return amount
    if state["cash"] < amount:
        return f"资金不足。当前现金 {state['cash']:,}，下注 {amount:,}。"

    legs = []
    odds = 1.0
    fair_odds = 1.0
    descriptions = []
    seen = set()
    for raw_index, pick in zip(indexes, picks):
        match = _match_by_display_index(state, raw_index)
        if not match:
            return f"比赛编号无效：{raw_index}。输入 schedule 查看当前轮。"
        if match["global_id"] in seen:
            return "同一场比赛不要在一个串关里反复横跳。"
        if pick not in {"home", "draw", "away"}:
            return "串关 pick 只支持 home / draw / away。"
        seen.add(match["global_id"])
        leg_odds = match["odds"]["wnl"][pick]
        leg_fair_odds = _fair_odds(match["probs"][pick])
        odds *= leg_odds
        fair_odds *= leg_fair_odds
        legs.append({"match_id": match["global_id"], "pick": pick, "odds": leg_odds, "fair_odds": leg_fair_odds})
        descriptions.append(f"{_team_name(match['home'])}-{_team_name(match['away'])}:{pick}")

    odds *= 0.97 ** (len(legs) - 1)
    odds = round(min(200.0, max(1.01, odds)), 2)
    cash_before = state["cash"]
    state["cash"] -= amount
    bet = {
        "id": state["next_bet_id"],
        "round_index": state["round_index"],
        "kind": "parlay",
        "match_id": None,
        "legs": legs,
        "pick": ",".join(picks),
        "amount": amount,
        "odds": odds,
        "fair_odds": fair_odds,
        "house_edge": _house_edge(amount, odds, fair_odds),
        "description": " / ".join(descriptions),
        "settled": False,
        "won": False,
        "profit": 0,
        "payout": 0,
        "cash_before": cash_before,
        "stage": state.get("phase", "unknown"),
    }
    state["next_bet_id"] += 1
    state["bets"].append(bet)
    _after_bet_placed(state, amount)
    return (
        f"串关下注成功 #{bet['id']}：{bet['description']}\n"
        f"金额 {amount:,}，组合赔率 {odds:.2f}。全中才赢，错一场就当给庄家买咖啡。\n"
        f"剩余现金：{state['cash']:,}"
    )


def _cmd_next(state: Dict[str, Any]) -> str:
    if state.get("ended"):
        return "游戏已结束。再 next 也不能把奖杯从博物馆里摇出来。"
    if not state.get("current_matches"):
        return "当前没有比赛可推进。"

    rng = RNG(state["rng_state"])
    round_index = state["round_index"]
    matches = state["current_matches"]
    cash_before = state["cash"]
    debt_before = state["debt"]
    titles_before = set(state["permanent_titles"])
    lines = [f"⏭️ 推进第 {round_index + 1} 轮 · {_round_name(state)}", ""]
    results_by_id = {}

    for match in matches:
        result = _simulate_match(match, rng)
        match["result"] = result
        state["all_matches"].append(match)
        results_by_id[match["global_id"]] = match
        lines.append(_format_match_result(match))
        if match["stage"] == "group":
            _apply_group_result(state, match)
        else:
            _apply_knockout_result(state, match)

    settlement_lines, round_profit = _settle_round_bets(state, round_index, results_by_id)
    if settlement_lines:
        lines.append("")
        lines.append("💰 结算")
        lines.extend(settlement_lines)
    else:
        lines.append("")
        lines.append("本轮没有下注。恭喜你短暂战胜了自己。")

    interest = 0
    if state["debt"] > 0:
        old_debt = state["debt"]
        state["debt"] = int(math.ceil(state["debt"] * (1 + LOAN_RATE)))
        interest = state["debt"] - old_debt
        lines.append(f"高利贷利息 +{interest:,}，当前债务 {state['debt']:,}。")

    _update_round_titles(state, round_index)
    state["round_index"] += 1
    state["rng_state"] = rng.state

    if state["debt"] >= DEBT_LIMIT or _net_assets(state) <= -DEBT_LIMIT:
        state["ended"] = True
        state["phase"] = "ended"
        state["current_matches"] = []
        state["round_news"] = []
        _add_title(state, "hopeless")
        lines.append("")
        lines.append("💀 债务击穿 -500000 红线，游戏强制结束。庄家甚至有点同情你。")
    elif state["round_index"] >= 17:
        state["ended"] = True
        state["phase"] = "ended"
        state["current_matches"] = []
        state["round_news"] = []
        lines.append("")
        champion = state.get("bracket", {}).get("champion")
        if champion:
            lines.append(f"🏆 本届虚拟世界杯冠军：{_team_name(champion)}")
        lines.append("世界杯结束。账单也结束了，除非你还欠着。")
    else:
        _prepare_current_round(state, rng)
        state["rng_state"] = rng.state
        lines.append("")
        lines.append(f"下一轮：{_round_name(state)}。输入 schedule 继续下注，输入 news 继续被传闻带节奏。")

    new_titles = [title for title in state["permanent_titles"] if title not in titles_before]
    if new_titles:
        lines.append("")
        for title in new_titles:
            lines.append(f"🏷️ 新称号解锁：{TITLE_NAMES.get(title, title)}")
            taunt = TITLE_TAUNTS.get(title)
            if taunt:
                lines.append(f"嘲讽语：{taunt}")

    mood = _mood_text(state, cash_before, debt_before, round_profit)
    lines.append("")
    lines.append(mood)
    if state["cash"] < MIN_BET and not state.get("ended"):
        lines.append("现金低于最低下注。你可以 loan，也可以 quit。一个伤钱包，一个伤自尊。")
    return "\n".join(lines)


def _cmd_history(state: Dict[str, Any]) -> str:
    bets = state["bets"][-20:]
    if not bets:
        return "还没有下注历史。此刻的你仍然清白。"
    lines = ["📜 最近下注记录（最多 20 条）"]
    for bet in bets:
        if bet["settled"]:
            result = "赢" if bet["won"] else "输"
            money = f"{bet['profit']:+,}"
        else:
            result = "待结算"
            money = "0"
        lines.append(
            f"#{bet['id']:03d} {bet['kind']} | {bet['description']} | "
            f"金额 {bet['amount']:,} | 赔率 {bet['odds']:.2f} | {result} | 盈亏 {money}"
        )
    return "\n".join(lines)


def _cmd_summary(state: Dict[str, Any]) -> str:
    settled = [bet for bet in state["bets"] if bet["settled"]]
    wins = sum(1 for bet in settled if bet["won"])
    losses = len(settled) - wins
    win_rate = (wins / len(settled) * 100) if settled else 0.0
    total_staked = sum(bet["amount"] for bet in state["bets"])
    total_returned = sum(bet.get("payout", 0) for bet in settled)
    titles = [TITLE_NAMES.get(title, title) for title in state.get("permanent_titles", [])]
    return "\n".join(
        [
            "📈 完整统计摘要",
            f"总下注次数：{len(state['bets'])}",
            f"已结算下注：{len(settled)}",
            f"胜：{wins}",
            f"负：{losses}",
            f"胜率：{win_rate:.1f}%",
            f"总投入：{total_staked:,}",
            f"总返还：{total_returned:,}",
            f"累计盈亏：{state['total_profit']:+,}",
            _house_edge_line(state),
            f"最大单笔盈利：{state['max_single_win']:+,}",
            f"最大单笔亏损：{state['max_single_loss']:+,}",
            f"最终/当前现金：{state['cash']:,}",
            f"债务：{state['debt']:,}",
            f"净资产：{_net_assets(state):,}",
            "已获永久称号：" + ("、".join(titles) if titles else "暂无"),
        ]
    )


def _cmd_titles(state: Dict[str, Any]) -> str:
    _refresh_dynamic_titles(state)
    dynamic = state.get("dynamic_title", "steady")
    lines = ["🏷️ 称号系统", "", "动态资产称号："]
    lines.append(f"- {dynamic}: {TITLE_NAMES[dynamic]}")
    if state["debt"] > 0 and dynamic != "dog_end":
        lines.append(f"- dog_end: {TITLE_NAMES['dog_end']}")
    if state.get("loan_taken"):
        lines.append(f"- loan_vip: {TITLE_NAMES['loan_vip']}")
    lines.append("")
    lines.append("永久行为称号：")
    if state["permanent_titles"]:
        for title in state["permanent_titles"]:
            lines.append(f"- {title}: {TITLE_NAMES[title]} — {TITLE_TAUNTS.get(title, '')}")
    else:
        lines.append("- 暂无。你还没做出足够离谱的行为。")
    return "\n".join(lines)


def _cmd_news(state: Dict[str, Any]) -> str:
    if state.get("ended"):
        return "比赛结束后新闻只剩复盘。复盘通常比下注理性。"
    news = state.get("round_news", [])
    if not news:
        return "当前没有新闻。没有消息也是消息，但通常没什么用。"
    lines = [
        f"📰 第 {state['round_index'] + 1} 轮新闻/传闻",
        "提示：新闻真假混杂，赔率不会告诉你哪条有料。亏了可以怪记者，但记者不会赔。",
    ]
    lines.extend(f"- {item}" for item in news)
    return "\n".join(lines)


def _json_response(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False)


def _status_data(state: Dict[str, Any]) -> Dict[str, Any]:
    _refresh_dynamic_titles(state)
    settled = [bet for bet in state["bets"] if bet["settled"]]
    wins = sum(1 for bet in settled if bet["won"])
    pending = sum(1 for bet in state["bets"] if not bet["settled"])
    return {
        "cash": state["cash"],
        "debt": state["debt"],
        "net_assets": _net_assets(state),
        "round_index": state["round_index"],
        "round_number": state["round_index"] + 1 if not state.get("ended") else None,
        "total_rounds": 17,
        "phase": state.get("phase"),
        "stage": _round_name(state),
        "dynamic_title": state.get("dynamic_title", "steady"),
        "dynamic_title_name": TITLE_NAMES.get(state.get("dynamic_title", "steady")),
        "permanent_titles": [
            {"id": title, "name": TITLE_NAMES.get(title, title)}
            for title in state.get("permanent_titles", [])
        ],
        "total_profit": state["total_profit"],
        "win_rate": (wins / len(settled) * 100) if settled else 0.0,
        "wins": wins,
        "losses": len(settled) - wins,
        "bets_total": len(state["bets"]),
        "bets_settled": len(settled),
        "bets_pending": pending,
        "max_single_win": state["max_single_win"],
        "max_single_loss": state["max_single_loss"],
        "house_edge_total": _house_edge_total(state),
        "ended": bool(state.get("ended")),
    }


def _schedule_data(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "round_index": state["round_index"],
        "round_number": state["round_index"] + 1 if not state.get("ended") else None,
        "total_rounds": 17,
        "phase": state.get("phase"),
        "stage": _round_name(state),
        "ended": bool(state.get("ended")),
        "matches": [_match_public_data(match, index) for index, match in enumerate(state.get("current_matches", []), 1)],
    }


def _standings_data(state: Dict[str, Any]) -> Dict[str, Any]:
    groups = {}
    for group in GROUPS:
        groups[group] = [
            {
                "team_id": team_id,
                "team_name": _team_name(team_id),
                **state["standings"][group][team_id],
            }
            for team_id in _sorted_group(state, group)
        ]
    return {
        "round_index": state["round_index"],
        "round_number": state["round_index"] + 1 if not state.get("ended") else None,
        "phase": state.get("phase"),
        "stage": _round_name(state),
        "groups": groups,
        "bracket": state.get("bracket", {}),
        "played_matches": [_match_public_data(match, None) for match in state.get("all_matches", [])],
        "current_matches": [_match_public_data(match, index) for index, match in enumerate(state.get("current_matches", []), 1)],
    }


def _news_data(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "round_index": state["round_index"],
        "round_number": state["round_index"] + 1 if not state.get("ended") else None,
        "stage": _round_name(state),
        "items": list(state.get("round_news", [])),
    }


def _history_data(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "recent_limit": 20,
        "bets": [_bet_public_data(bet) for bet in state["bets"][-20:]],
    }


def _summary_data(state: Dict[str, Any]) -> Dict[str, Any]:
    settled = [bet for bet in state["bets"] if bet["settled"]]
    wins = sum(1 for bet in settled if bet["won"])
    total_staked = sum(bet["amount"] for bet in state["bets"])
    total_returned = sum(bet.get("payout", 0) for bet in settled)
    return {
        "bets_total": len(state["bets"]),
        "bets_settled": len(settled),
        "wins": wins,
        "losses": len(settled) - wins,
        "win_rate": (wins / len(settled) * 100) if settled else 0.0,
        "total_staked": total_staked,
        "total_returned": total_returned,
        "total_profit": state["total_profit"],
        "max_single_win": state["max_single_win"],
        "max_single_loss": state["max_single_loss"],
        "cash": state["cash"],
        "debt": state["debt"],
        "net_assets": _net_assets(state),
        "house_edge_total": _house_edge_total(state),
        "permanent_titles": [
            {"id": title, "name": TITLE_NAMES.get(title, title)}
            for title in state.get("permanent_titles", [])
        ],
    }


def _titles_data(state: Dict[str, Any]) -> Dict[str, Any]:
    _refresh_dynamic_titles(state)
    return {
        "dynamic": {"id": state.get("dynamic_title", "steady"), "name": TITLE_NAMES[state.get("dynamic_title", "steady")]},
        "debt_titles": [
            {"id": title, "name": TITLE_NAMES[title]}
            for title in ["dog_end", "loan_vip"]
            if (title == "dog_end" and state["debt"] > 0) or (title == "loan_vip" and state.get("loan_taken"))
        ],
        "permanent": [
            {"id": title, "name": TITLE_NAMES[title], "taunt": TITLE_TAUNTS.get(title, "")}
            for title in state.get("permanent_titles", [])
        ],
    }


def _match_public_data(match: Dict[str, Any], index: Optional[int]) -> Dict[str, Any]:
    data = {
        "index": index,
        "match_id": match["global_id"],
        "round_index": match["round_index"],
        "stage": match["stage"],
        "stage_label": match["stage_label"],
        "group": match.get("group"),
        "home": _team_public_data(match["home"]),
        "away": _team_public_data(match["away"]),
        "odds": _odds_public_data(match.get("odds", {})),
    }
    if match.get("result"):
        data["result"] = _result_public_data(match)
    return data


def _team_public_data(team_id: str) -> Dict[str, Any]:
    team = TEAM_BY_ID[team_id]
    return {"id": team_id, "name": team["name"], "power": team["power"], "tier": team["tier"]}


def _odds_public_data(odds: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "wnl": {key: float(value) for key, value in odds.get("wnl", {}).items()},
        "goals": {key: float(value) for key, value in odds.get("goals", {}).items()},
        "pk": {key: float(value) for key, value in odds.get("pk", {}).items()},
        "score_examples": {key: float(value) for key, value in odds.get("score_examples", {}).items()},
    }


def _result_public_data(match: Dict[str, Any]) -> Dict[str, Any]:
    result = match["result"]
    return {
        "home_goals": result["home_goals"],
        "away_goals": result["away_goals"],
        "wnl": result["wnl"],
        "went_extra": result["went_extra"],
        "went_pk": result["went_pk"],
        "extra_home": result["extra_home"],
        "extra_away": result["extra_away"],
        "pk_home": result["pk_home"],
        "pk_away": result["pk_away"],
        "winner": result["winner"],
        "winner_team": result["winner_team"],
        "loser_team": result["loser_team"],
    }


def _bet_public_data(bet: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": bet["id"],
        "round_index": bet["round_index"],
        "kind": bet["kind"],
        "match_id": bet.get("match_id"),
        "legs": bet.get("legs", []),
        "pick": bet["pick"],
        "amount": bet["amount"],
        "odds": bet["odds"],
        "fair_odds": bet.get("fair_odds"),
        "house_edge": bet.get("house_edge", 0),
        "description": bet["description"],
        "settled": bet["settled"],
        "won": bet["won"],
        "profit": bet["profit"],
        "payout": bet["payout"],
        "stage": bet.get("stage"),
    }


def _cmd_loan(state: Dict[str, Any]) -> str:
    if state.get("ended"):
        return "游戏已经结束。高利贷也要讲基本流程。"
    if state["cash"] >= MIN_BET:
        return f"你还有现金 {state['cash']:,}，暂时不能借高利贷。先亏到低于最低下注再说，别急。"
    state["cash"] += LOAN_AMOUNT
    state["debt"] += LOAN_AMOUNT
    state["loan_taken"] = True
    _refresh_dynamic_titles(state)
    if state["debt"] >= DEBT_LIMIT or _net_assets(state) <= -DEBT_LIMIT:
        state["ended"] = True
        state["phase"] = "ended"
        _add_title(state, "hopeless")
    return (
        f"💳 高利贷到账：+{LOAN_AMOUNT:,}\n"
        f"当前现金：{state['cash']:,}，债务：{state['debt']:,}。\n"
        f"每轮 10% 复利。数学不会怜悯赌狗。"
    )


def _cmd_repay(state: Dict[str, Any], parts: List[str]) -> str:
    if len(parts) != 2:
        return "用法：repay <amount>，例如：repay 10000"
    amount = _parse_amount(parts[1], allow_large=True)
    if isinstance(amount, str):
        return amount
    if state["debt"] <= 0:
        return "你没有债务。罕见的好消息。"
    if amount > state["cash"]:
        return f"还款金额不能超过当前现金。当前现金 {state['cash']:,}。"
    if amount > state["debt"]:
        return f"还款金额不能超过债务。当前债务 {state['debt']:,}。"
    state["cash"] -= amount
    state["debt"] -= amount
    _refresh_dynamic_titles(state)
    return f"还款成功：-{amount:,}。当前现金 {state['cash']:,}，债务 {state['debt']:,}。"


def _cmd_quit(state: Dict[str, Any]) -> str:
    state["ended"] = True
    state["phase"] = "ended"
    _refresh_dynamic_titles(state)
    settled = [bet for bet in state["bets"] if bet["settled"]]
    wins = sum(1 for bet in settled if bet["won"])
    win_rate = (wins / len(settled) * 100) if settled else 0.0
    titles = [TITLE_NAMES.get(t, t) for t in state.get("permanent_titles", [])]
    if state.get("dynamic_title"):
        titles.insert(0, TITLE_NAMES[state["dynamic_title"]])
    return "\n".join(
        [
            "🏁 游戏结束",
            f"最终现金：{state['cash']:,}",
            f"最终债务：{state['debt']:,}",
            f"最终净资产：{_net_assets(state):,}",
            f"总盈亏：{state['total_profit']:+,}",
            _house_edge_line(state),
            f"战绩：{wins}/{len(settled)}，胜率 {win_rate:.1f}%",
            "称号：" + ("、".join(titles) if titles else "暂无"),
            "免责声明：这只是虚拟模拟器。现实里别赌，现实里的庄家可不会给你 README。",
        ]
    )


def _help_text() -> str:
    return """⚽ 赌狗的自我修养 · AI 世界杯赌球模拟器

这是虚拟游戏，不涉及真实金钱，不提供任何现实赌博建议。
AI agent 可以只通过 print(gambler.cmd("...")) 进行纯文本交互。

基础规则：
- 16 支虚构球队，4 个实力档位。
- 小组赛 12 轮，每轮 2 场；每组前 2 名出线。
- 淘汰赛 5 轮，共 10 场；90 分钟可平，加时/点球决定晋级。
- 起始资金 100000，单注最低 100。
- 庄家赔率有抽水，长期期望为负。是的，庄家不是来做慈善的。
- 同 seed + 同命令序列 = 同结果；存档为 gambler_save.json。

命令列表：
new_game <seed>                         新开一局并覆盖旧存档
help                                    查看说明
status                                  查看资金、债务、称号、盈亏
schedule                                查看当前轮可下注比赛和赔率
standings                               查看积分榜或淘汰赛对阵
news                                    查看本轮新闻/传闻
bet wnl <match> <home/draw/away> <amt>  胜平负
bet score <match> <2-1> <amt>           猜具体比分
bet goals <match> <over3/under3> <amt>  猜总进球，严格大于/小于盘口
bet pk <match> <yes/no> <amt>           猜点球大战，仅淘汰赛
parlay <1,2,3> <home,away,home> <amt>   串关，全中才赢
next                                    推进一轮并结算
history                                 最近 20 条下注记录
summary                                 完整统计摘要
titles                                  查看称号
loan                                    现金 < 100 时借 50000 高利贷
repay <amount>                          还款
quit                                    结束游戏

示例：
bet wnl 1 home 5000
bet score 1 2-1 1000
bet goals 1 over3 2000
parlay 1,2 home,away 3000

查询命令可加 --json：schedule --json / status --json / news --json / summary --json

友情提示：新闻负责煽风点火，结果负责冷水浇头。"""


def _parse_seed(raw: str) -> int:
    try:
        return int(raw)
    except ValueError:
        value = 0
        for char in raw:
            value = ((value * 131) + ord(char)) & 0xFFFFFFFF
        return value


def _new_state(seed: int) -> Dict[str, Any]:
    rng = RNG(seed)
    groups = _draw_groups(rng)
    news_signal_config = _new_news_signal_config(rng)
    standings = {
        group: {
            team_id: {"played": 0, "pts": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "gd": 0}
            for team_id in teams
        }
        for group, teams in groups.items()
    }
    state: Dict[str, Any] = {
        "version": 1,
        "seed": seed,
        "rng_state": rng.state,
        "cash": STARTING_CASH,
        "debt": 0,
        "total_profit": 0,
        "max_single_win": 0,
        "max_single_loss": 0,
        "phase": "group",
        "round_index": 0,
        "groups": groups,
        "standings": standings,
        "bracket": {},
        "current_matches": [],
        "all_matches": [],
        "round_news": [],
        "round_news_signals": [],
        "round_power_mods": {},
        "news_signal_config": news_signal_config,
        "bets": [],
        "next_bet_id": 1,
        "next_match_id": 1,
        "permanent_titles": [],
        "dynamic_title": "steady",
        "loan_taken": False,
        "ended": False,
        "win_streak": 0,
        "loss_streak": 0,
        "last_bet_amount": 0,
        "first_bet_settled": False,
        "group_wnl_count": 0,
        "group_wnl_wins": 0,
        "conservative_rounds": 0,
    }
    rng = RNG(state["rng_state"])
    _prepare_current_round(state, rng)
    state["rng_state"] = rng.state
    _refresh_dynamic_titles(state)
    return state


def _new_news_signal_config(rng: RNG) -> Dict[str, Any]:
    sources = list(NEWS_SOURCES)
    rng.shuffle(sources)
    reliable_sources = sources[:1]
    source_reliability = {source: (1.0 if source in reliable_sources else 0.0) for source in NEWS_SOURCES}
    return {
        "truth_rate": 0.25,
        "positive_delta": [10, 12],
        "negative_delta": [-12, -10],
        "source_reliability": source_reliability,
        "reliable_sources": reliable_sources,
        "salt": rng.randint(1, 2_147_483_647),
    }


def _draw_groups(rng: RNG) -> Dict[str, List[str]]:
    tiers: List[List[str]] = []
    for tier in [1, 2, 3, 4]:
        team_ids = [team["id"] for team in TEAMS if team["tier"] == tier]
        rng.shuffle(team_ids)
        tiers.append(team_ids)

    groups = {group: [] for group in GROUPS}
    for tier_teams in tiers:
        for index, group in enumerate(GROUPS):
            groups[group].append(tier_teams[index])
    for group in GROUPS:
        rng.shuffle(groups[group])
    return groups


def _prepare_current_round(state: Dict[str, Any], rng: RNG) -> None:
    round_index = state["round_index"]
    if round_index < 12:
        state["phase"] = "group"
        state["current_matches"] = _make_group_round(state, rng, round_index)
    elif round_index <= 16:
        state["phase"] = "knockout"
        if not state.get("bracket"):
            _create_knockout_bracket(state)
        state["current_matches"] = _make_knockout_round(state, rng, round_index)
    else:
        state["phase"] = "ended"
        state["current_matches"] = []
        state["ended"] = True
    if not state.get("ended"):
        state["round_news"] = _generate_news(state, rng)


def _make_group_round(state: Dict[str, Any], rng: RNG, round_index: int) -> List[Dict[str, Any]]:
    group = GROUPS[round_index % 4]
    group_round = round_index // 4
    teams = state["groups"][group]
    matches = []
    for home_pos, away_pos in GROUP_PAIRINGS[group_round]:
        matches.append(
            _new_match(
                state,
                rng,
                teams[home_pos],
                teams[away_pos],
                "group",
                f"小组赛 {group}组第{group_round + 1}轮",
                group=group,
            )
        )
    return matches


def _create_knockout_bracket(state: Dict[str, Any]) -> None:
    qualified = []
    for group in GROUPS:
        ranked = _sorted_group(state, group)
        qualified.extend(ranked[:2])
    # Cross-group bracket: A1-B2, B1-A2, C1-D2, D1-C2.
    q = {
        "A1": _sorted_group(state, "A")[0],
        "A2": _sorted_group(state, "A")[1],
        "B1": _sorted_group(state, "B")[0],
        "B2": _sorted_group(state, "B")[1],
        "C1": _sorted_group(state, "C")[0],
        "C2": _sorted_group(state, "C")[1],
        "D1": _sorted_group(state, "D")[0],
        "D2": _sorted_group(state, "D")[1],
    }
    state["bracket"] = {
        "qualified": qualified,
        "qf_pairs": [(q["A1"], q["B2"]), (q["B1"], q["A2"]), (q["C1"], q["D2"]), (q["D1"], q["C2"])],
        "qf_winners": [],
        "qf_losers": [],
        "four_winners": [],
        "four_losers": [],
        "placement_winners": [],
        "placement_losers": [],
        "champion": None,
        "runner_up": None,
        "third": None,
        "fourth": None,
    }


def _make_knockout_round(state: Dict[str, Any], rng: RNG, round_index: int) -> List[Dict[str, Any]]:
    stage, label, _ = KNOCKOUT_INFO[round_index]
    bracket = state["bracket"]
    if stage == "qf":
        pairs = bracket["qf_pairs"]
    elif stage == "four":
        winners = bracket["qf_winners"]
        pairs = [(winners[0], winners[3]), (winners[1], winners[2])] if len(winners) >= 4 else []
    elif stage == "placement":
        losers = bracket["qf_losers"]
        pairs = [(losers[0], losers[3]), (losers[1], losers[2])] if len(losers) >= 4 else []
    elif stage == "third":
        losers = bracket["four_losers"]
        pairs = [(losers[0], losers[1])] if len(losers) >= 2 else []
    elif stage == "final":
        winners = bracket["four_winners"]
        pairs = [(winners[0], winners[1])] if len(winners) >= 2 else []
    else:
        pairs = []

    matches = []
    for home, away in pairs:
        matches.append(_new_match(state, rng, home, away, stage, label))
    return matches


def _new_match(
    state: Dict[str, Any],
    rng: RNG,
    home: str,
    away: str,
    stage: str,
    stage_label: str,
    group: Optional[str] = None,
) -> Dict[str, Any]:
    probs = _wnl_probs(home, away)
    fluct = {
        "wnl": {key: rng.uniform(0.95, 1.05) for key in ["home", "draw", "away"]},
        "score": rng.uniform(0.95, 1.05),
        "goals": {key: rng.uniform(0.95, 1.05) for key in _goals_keys()},
        "pk": {key: rng.uniform(0.95, 1.05) for key in ["yes", "no"]},
    }
    match = {
        "global_id": state["next_match_id"],
        "round_index": state["round_index"],
        "stage": stage,
        "stage_label": stage_label,
        "group": group,
        "home": home,
        "away": away,
        "probs": probs,
        "fluct": fluct,
        "odds": {},
        "result": None,
    }
    state["next_match_id"] += 1
    match["odds"] = _make_odds(match)
    return match


def _make_odds(match: Dict[str, Any]) -> Dict[str, Any]:
    probs = match["probs"]
    wnl = {
        outcome: _odds(probs[outcome], 0.90, 1.20, 8.00, match["fluct"]["wnl"][outcome])
        for outcome in ["home", "draw", "away"]
    }
    goals = {key: _goals_odds(match, *(_parse_goals_pick(key) or ("over", 2))) for key in _goals_keys()}
    pk_prob_yes = probs["draw"] * 0.50
    pk = {
        "yes": _odds(pk_prob_yes, 0.88, 2.50, 4.00, match["fluct"]["pk"]["yes"]),
        "no": _odds(max(0.01, 1 - pk_prob_yes), 0.88, 1.08, 1.60, match["fluct"]["pk"]["no"]),
    }
    examples = {}
    for score in ["1-0", "2-1", "1-1", "0-1"]:
        h, a = [int(x) for x in score.split("-")]
        examples[score] = _score_odds(match, h, a)
    return {"wnl": wnl, "goals": goals, "pk": pk, "score_examples": examples}


def _wnl_probs(home: str, away: str, power_mods: Optional[Dict[str, int]] = None) -> Dict[str, float]:
    power_mods = power_mods or {}
    home_power = TEAM_BY_ID[home]["power"] + int(power_mods.get("home", 0))
    away_power = TEAM_BY_ID[away]["power"] + int(power_mods.get("away", 0))
    home_advantage = 3.5
    power_diff = home_power - away_power + home_advantage
    base_home = 1 / (1 + 10 ** (-power_diff / 20))
    draw = 0.25
    home_win = (1 - draw) * base_home
    away_win = (1 - draw) * (1 - base_home)
    # A 17% upset blend narrows favorites and keeps underdogs alive.
    upset = 0.17
    mixed_home = home_win * (1 - upset) + away_win * upset
    mixed_away = away_win * (1 - upset) + home_win * upset
    total = mixed_home + mixed_away + draw
    return {"home": mixed_home / total, "draw": draw / total, "away": mixed_away / total}


def _expected_goals(home: str, away: str, power_mods: Optional[Dict[str, int]] = None) -> Tuple[float, float]:
    power_mods = power_mods or {}
    hp = TEAM_BY_ID[home]["power"] + int(power_mods.get("home", 0))
    ap = TEAM_BY_ID[away]["power"] + int(power_mods.get("away", 0))
    diff = (hp - ap) / 10
    home_lambda = 1.05 + (hp - 75) / 100 + max(diff, 0) * 0.10 + 0.08
    away_lambda = 0.95 + (ap - 75) / 105 + max(-diff, 0) * 0.10
    return (_clamp(home_lambda, 0.35, 2.05), _clamp(away_lambda, 0.30, 1.95))


def _score_probability(match: Dict[str, Any], home_goals: int, away_goals: int) -> float:
    home_lambda, away_lambda = _expected_goals(match["home"], match["away"])
    return _poisson_pmf(home_goals, home_lambda) * _poisson_pmf(away_goals, away_lambda)


def _score_odds(match: Dict[str, Any], home_goals: int, away_goals: int) -> float:
    probability = _score_probability(match, home_goals, away_goals)
    return _odds(probability, 0.85, 5.00, 50.00, match["fluct"]["score"])


def _goals_keys() -> List[str]:
    return ["over1", "over2", "over3", "under1", "under2", "under3", "under4"]


def _goals_odds(match: Dict[str, Any], mode: str, line: int) -> float:
    probability = _goals_probability(match, mode, line)
    key = f"{mode}{line}"
    fluct = match["fluct"]["goals"].get(key, 1.0)
    return _odds(probability, 0.88, 1.60, 3.00, fluct)


def _goals_probability(match: Dict[str, Any], mode: str, line: int) -> float:
    home_lambda, away_lambda = _expected_goals(match["home"], match["away"])
    total_lambda = home_lambda + away_lambda
    if mode == "over":
        return 1 - sum(_poisson_pmf(i, total_lambda) for i in range(line + 1))
    return sum(_poisson_pmf(i, total_lambda) for i in range(line))


def _simulation_probs(match: Dict[str, Any]) -> Dict[str, float]:
    return _wnl_probs(match["home"], match["away"], _match_power_mods(match))


def _match_power_mods(match: Dict[str, Any]) -> Dict[str, int]:
    mods = match.get("power_mods") or {}
    return {"home": int(mods.get("home", 0)), "away": int(mods.get("away", 0))}


def _simulate_match(match: Dict[str, Any], rng: RNG) -> Dict[str, Any]:
    roll = rng.random()
    probs = _simulation_probs(match)
    if roll < probs["home"]:
        wnl = "home"
    elif roll < probs["home"] + probs["draw"]:
        wnl = "draw"
    else:
        wnl = "away"
    home_goals, away_goals = _generate_score(match, rng, wnl)
    result = {
        "home_goals": home_goals,
        "away_goals": away_goals,
        "wnl": wnl,
        "went_extra": False,
        "went_pk": False,
        "extra_home": 0,
        "extra_away": 0,
        "pk_home": 0,
        "pk_away": 0,
        "winner": None,
        "winner_team": None,
        "loser_team": None,
    }
    if match["stage"] == "group":
        if wnl == "home":
            result["winner"] = "home"
            result["winner_team"] = match["home"]
            result["loser_team"] = match["away"]
        elif wnl == "away":
            result["winner"] = "away"
            result["winner_team"] = match["away"]
            result["loser_team"] = match["home"]
        return result

    if wnl == "home":
        winner = "home"
    elif wnl == "away":
        winner = "away"
    else:
        result["went_extra"] = True
        if rng.random() < 0.50:
            result["went_pk"] = True
            winner = _winner_by_power(match, rng)
            loser = "away" if winner == "home" else "home"
            win_pk = rng.randint(4, 6)
            lose_pk = rng.randint(2, win_pk - 1)
            result[f"pk_{winner}"] = win_pk
            result[f"pk_{loser}"] = lose_pk
        else:
            winner = _winner_by_power(match, rng)
            result[f"extra_{winner}"] = 1
    loser = "away" if winner == "home" else "home"
    result["winner"] = winner
    result["winner_team"] = match[winner]
    result["loser_team"] = match[loser]
    return result


def _generate_score(match: Dict[str, Any], rng: RNG, wnl: str) -> Tuple[int, int]:
    home_lambda, away_lambda = _expected_goals(match["home"], match["away"], _match_power_mods(match))
    home_goals = _poisson_sample(rng, home_lambda)
    away_goals = _poisson_sample(rng, away_lambda)
    if wnl == "draw":
        goals = max(0, min(5, int(round((home_goals + away_goals) / 2))))
        return goals, goals
    if wnl == "home":
        if home_goals <= away_goals:
            home_goals = away_goals + 1 + rng.randint(0, 1)
    else:
        if away_goals <= home_goals:
            away_goals = home_goals + 1 + rng.randint(0, 1)
    return _tame_score(home_goals, away_goals, wnl)


def _tame_score(home_goals: int, away_goals: int, wnl: str) -> Tuple[int, int]:
    """Keep football scores plausible while preserving the simulated result."""
    if wnl == "draw":
        goals = min(home_goals, 3)
        return goals, goals

    while home_goals + away_goals > 6:
        if wnl == "home":
            if home_goals > away_goals + 1:
                home_goals -= 1
            elif away_goals > 0:
                away_goals -= 1
            else:
                break
        else:
            if away_goals > home_goals + 1:
                away_goals -= 1
            elif home_goals > 0:
                home_goals -= 1
            else:
                break
    return home_goals, away_goals


def _winner_by_power(match: Dict[str, Any], rng: RNG) -> str:
    power_mods = _match_power_mods(match)
    home_power = TEAM_BY_ID[match["home"]]["power"] + int(power_mods.get("home", 0))
    away_power = TEAM_BY_ID[match["away"]]["power"] + int(power_mods.get("away", 0))
    probability = 1 / (1 + 10 ** (-(home_power - away_power) / 22))
    return "home" if rng.random() < probability else "away"


def _apply_group_result(state: Dict[str, Any], match: Dict[str, Any]) -> None:
    group = match["group"]
    home = match["home"]
    away = match["away"]
    result = match["result"]
    hg = result["home_goals"]
    ag = result["away_goals"]
    home_row = state["standings"][group][home]
    away_row = state["standings"][group][away]
    home_row["played"] += 1
    away_row["played"] += 1
    home_row["gf"] += hg
    home_row["ga"] += ag
    away_row["gf"] += ag
    away_row["ga"] += hg
    home_row["gd"] = home_row["gf"] - home_row["ga"]
    away_row["gd"] = away_row["gf"] - away_row["ga"]
    if hg > ag:
        home_row["pts"] += 3
        home_row["w"] += 1
        away_row["l"] += 1
    elif hg < ag:
        away_row["pts"] += 3
        away_row["w"] += 1
        home_row["l"] += 1
    else:
        home_row["pts"] += 1
        away_row["pts"] += 1
        home_row["d"] += 1
        away_row["d"] += 1


def _apply_knockout_result(state: Dict[str, Any], match: Dict[str, Any]) -> None:
    bracket = state["bracket"]
    result = match["result"]
    winner = result["winner_team"]
    loser = result["loser_team"]
    if match["stage"] == "qf":
        bracket["qf_winners"].append(winner)
        bracket["qf_losers"].append(loser)
    elif match["stage"] == "four":
        bracket["four_winners"].append(winner)
        bracket["four_losers"].append(loser)
    elif match["stage"] == "placement":
        bracket["placement_winners"].append(winner)
        bracket["placement_losers"].append(loser)
    elif match["stage"] == "third":
        bracket["third"] = winner
        bracket["fourth"] = loser
    elif match["stage"] == "final":
        bracket["champion"] = winner
        bracket["runner_up"] = loser


def _settle_round_bets(
    state: Dict[str, Any], round_index: int, results_by_id: Dict[int, Dict[str, Any]]
) -> Tuple[List[str], int]:
    lines = []
    round_profit = 0
    for bet in state["bets"]:
        if bet["settled"] or bet["round_index"] != round_index:
            continue
        won = _evaluate_bet(bet, results_by_id)
        payout = int(round(bet["amount"] * bet["odds"])) if won else 0
        profit = payout - bet["amount"] if won else -bet["amount"]
        if won:
            state["cash"] += payout
            state["win_streak"] += 1
            state["loss_streak"] = 0
            if state["win_streak"] >= 3:
                _add_title(state, "paul")
        else:
            state["loss_streak"] += 1
            state["win_streak"] = 0
            if state["loss_streak"] >= 5:
                _add_title(state, "reverse")

        bet["settled"] = True
        bet["won"] = won
        bet["payout"] = payout
        bet["profit"] = profit
        state["total_profit"] += profit
        state["max_single_win"] = max(state["max_single_win"], profit)
        state["max_single_loss"] = min(state["max_single_loss"], profit)
        round_profit += profit

        if not state["first_bet_settled"]:
            state["first_bet_settled"] = True
            if won:
                _add_title(state, "beginner_luck")
        if bet["kind"] == "parlay" and won:
            _add_title(state, "emperor")
        if bet["kind"] == "wnl":
            match = results_by_id.get(bet["match_id"])
            if match and match["stage"] == "group":
                state["group_wnl_count"] += 1
                if won:
                    state["group_wnl_wins"] += 1
                if state["group_wnl_count"] >= 6 and state["group_wnl_wins"] == state["group_wnl_count"]:
                    _add_title(state, "all_correct_group")
        if _bet_touches_final_and_won(bet, results_by_id, won):
            _add_title(state, "champion_predict")
        if bet["cash_before"] <= bet["amount"] and not won and state["cash"] <= 0:
            _add_title(state, "yolo")
        if state.get("loan_taken") and state["cash"] <= 0 and not won:
            _add_title(state, "hopeless")

        outcome = "✅ 赢" if won else "❌ 输"
        lines.append(
            f"{outcome} #{bet['id']} {bet['kind']} | {bet['description']} | "
            f"赔率 {bet['odds']:.2f} | 盈亏 {profit:+,}"
        )
    _refresh_streak_titles_from_history(state)
    return lines, round_profit


def _refresh_streak_titles_from_history(state: Dict[str, Any]) -> None:
    max_wins = 0
    max_losses = 0
    current_wins = 0
    current_losses = 0
    for bet in sorted((bet for bet in state["bets"] if bet["settled"]), key=lambda item: item["id"]):
        if bet["kind"] == "pk":
            continue
        if bet["won"]:
            current_wins += 1
            current_losses = 0
        else:
            current_losses += 1
            current_wins = 0
        max_wins = max(max_wins, current_wins)
        max_losses = max(max_losses, current_losses)
    if max_wins >= 3:
        _add_title(state, "paul")
    if max_losses >= 5:
        _add_title(state, "reverse")


def _evaluate_bet(bet: Dict[str, Any], results_by_id: Dict[int, Dict[str, Any]]) -> bool:
    if bet["kind"] == "parlay":
        for leg in bet["legs"]:
            match = results_by_id.get(leg["match_id"])
            if not match or match["result"]["wnl"] != leg["pick"]:
                return False
        return True

    match = results_by_id.get(bet["match_id"])
    if not match:
        return False
    result = match["result"]
    pick = bet["pick"]
    if bet["kind"] == "wnl":
        return result["wnl"] == pick
    if bet["kind"] == "score":
        return f"{result['home_goals']}-{result['away_goals']}" == pick
    if bet["kind"] == "goals":
        parsed = _parse_goals_pick(pick)
        if not parsed:
            return False
        mode, line = parsed
        total = result["home_goals"] + result["away_goals"]
        return total > line if mode == "over" else total < line
    if bet["kind"] == "pk":
        return result["went_pk"] == (pick == "yes")
    return False


def _place_bet(
    state: Dict[str, Any],
    kind: str,
    amount: int,
    odds: float,
    fair_odds: float,
    description: str,
    match: Dict[str, Any],
    pick: str,
) -> str:
    cash_before = state["cash"]
    state["cash"] -= amount
    bet = {
        "id": state["next_bet_id"],
        "round_index": state["round_index"],
        "kind": kind,
        "match_id": match["global_id"],
        "legs": [],
        "pick": pick,
        "amount": amount,
        "odds": odds,
        "fair_odds": fair_odds,
        "house_edge": _house_edge(amount, odds, fair_odds),
        "description": description,
        "settled": False,
        "won": False,
        "profit": 0,
        "payout": 0,
        "cash_before": cash_before,
        "stage": match["stage"],
    }
    state["next_bet_id"] += 1
    state["bets"].append(bet)
    _after_bet_placed(state, amount)
    return (
        f"下注成功 #{bet['id']}：{kind} | {description}\n"
        f"金额 {amount:,}，赔率 {odds:.2f}。\n"
        f"剩余现金：{state['cash']:,}\n"
        f"{_bet_confirmation(state, bet['id'])}"
    )


def _after_bet_placed(state: Dict[str, Any], amount: int) -> None:
    if state["loss_streak"] >= 2 and state["last_bet_amount"] > 0 and amount >= state["last_bet_amount"] * 2:
        _add_title(state, "chaser")
    state["last_bet_amount"] = amount
    _refresh_dynamic_titles(state)


def _bet_confirmation(state: Dict[str, Any], bet_id: int) -> str:
    index = (int(state.get("seed", 0)) + bet_id * 7 + int(state.get("rng_state", 0))) % len(BET_CONFIRMATIONS)
    return BET_CONFIRMATIONS[index]


def _update_round_titles(state: Dict[str, Any], round_index: int) -> None:
    round_bets = [bet for bet in state["bets"] if bet["round_index"] == round_index]
    if round_bets and all(bet["amount"] == MIN_BET for bet in round_bets):
        state["conservative_rounds"] += 1
        if state["conservative_rounds"] >= 5:
            _add_title(state, "conservative")
    elif round_bets:
        state["conservative_rounds"] = 0
    _refresh_dynamic_titles(state)


def _bet_touches_final_and_won(
    bet: Dict[str, Any], results_by_id: Dict[int, Dict[str, Any]], won: bool
) -> bool:
    if not won:
        return False
    if bet["kind"] == "parlay":
        return any((results_by_id.get(leg["match_id"]) or {}).get("stage") == "final" for leg in bet["legs"])
    match = results_by_id.get(bet["match_id"])
    return bool(match and match["stage"] == "final")


def _generate_news(state: Dict[str, Any], rng: RNG) -> List[str]:
    matches = state.get("current_matches", [])
    state["round_news_signals"] = []
    state["round_power_mods"] = {}
    if not matches:
        return []
    count = rng.randint(2, 3)
    items = []
    seen = set()
    signals = []
    power_mods: Dict[str, int] = {}
    categories = list(NEWS.keys())
    attempts = 0
    max_attempts = count * 8
    while len(items) < count and attempts < max_attempts:
        attempts += 1
        match = rng.choice(matches)
        team_id = rng.choice([match["home"], match["away"]])
        category = rng.choice(categories)
        source = rng.choice(NEWS_SOURCES)
        icon, template = rng.choice(NEWS[category])
        if category == "match_event":
            item = f"{source}：{icon} {_team_name(match['home'])} vs {_team_name(match['away'])}：{template}"
        else:
            item = f"{source}：{icon} " + template.format(team=_team_name(team_id))
        if item in seen:
            continue
        seen.add(item)
        items.append(item)
        signal = _news_signal(state, rng, category, team_id, item, source)
        signals.append(signal)
        if signal["true"]:
            power_mods[team_id] = power_mods.get(team_id, 0) + signal["delta"]
    state["round_news_signals"] = signals
    state["round_power_mods"] = power_mods
    _attach_round_power_mods(state)
    return items


def _news_signal(
    state: Dict[str, Any], rng: RNG, category: str, team_id: str, text: str, source: str
) -> Dict[str, Any]:
    config = state.get("news_signal_config") or _new_news_signal_config(rng)
    if "news_signal_config" not in state:
        state["news_signal_config"] = config
    source_reliability = config.get("source_reliability") or {}
    if source_reliability:
        truth_probability = float(source_reliability.get(source, 0.0))
    else:
        truth_probability = float(config.get("truth_rate", 0.25))
    is_true = category in {"positive", "negative"} and rng.random() < truth_probability
    delta = 0
    if is_true and category == "positive":
        low, high = config.get("positive_delta", [2, 3])
        delta = rng.randint(int(low), int(high))
    elif is_true and category == "negative":
        low, high = config.get("negative_delta", [-3, -2])
        magnitude = rng.randint(abs(int(high)), abs(int(low)))
        delta = -magnitude
    return {"text": text, "source": source, "category": category, "team_id": team_id, "true": is_true, "delta": delta}


def _attach_round_power_mods(state: Dict[str, Any]) -> None:
    mods = state.get("round_power_mods", {})
    for match in state.get("current_matches", []):
        match["power_mods"] = {
            "home": int(mods.get(match["home"], 0)),
            "away": int(mods.get(match["away"], 0)),
        }


def _format_groups(state: Dict[str, Any]) -> str:
    lines = ["分组抽签完成："]
    for group in GROUPS:
        lines.append(f"Group {group}: " + "、".join(_team_name(team_id) for team_id in state["groups"][group]))
    return "\n".join(lines)


def _format_match_result(match: Dict[str, Any]) -> str:
    result = match["result"]
    home = _team_name(match["home"])
    away = _team_name(match["away"])
    score = f"{result['home_goals']}-{result['away_goals']}"
    text = f"{match['stage_label']} | {home} {score} {away}"
    if match["stage"] != "group":
        if result["went_pk"]:
            text += (
                f" | 点球 {result['pk_home']}-{result['pk_away']} | "
                f"晋级/胜者：{_team_name(result['winner_team'])}"
            )
        elif result["went_extra"]:
            extra_score = f"{result['extra_home']}-{result['extra_away']}"
            text += f" | 加时 {extra_score} | 晋级/胜者：{_team_name(result['winner_team'])}"
        else:
            text += f" | 晋级/胜者：{_team_name(result['winner_team'])}"
    return text


def _round_name(state: Dict[str, Any]) -> str:
    if state.get("ended"):
        return "已结束"
    round_index = state["round_index"]
    if round_index < 12:
        group = GROUPS[round_index % 4]
        group_round = round_index // 4 + 1
        return f"小组赛 {group}组第{group_round}轮"
    info = KNOCKOUT_INFO.get(round_index)
    if info:
        return info[1]
    return "未知阶段"


def _mood_text(state: Dict[str, Any], cash_before: int, debt_before: int, round_profit: int) -> str:
    if state["cash"] <= 0 and not state.get("ended"):
        bucket = "broke"
    elif state["debt"] > debt_before or state["debt"] > 0:
        bucket = "in_debt"
    elif round_profit >= max(10_000, cash_before * 0.15):
        bucket = "big_win"
    elif round_profit > 0:
        bucket = "small_win"
    elif round_profit <= -max(10_000, max(1, cash_before) * 0.15):
        bucket = "big_loss"
    else:
        bucket = "small_loss"
    rng = RNG((state["rng_state"] + state["round_index"] * 2654435761) & 0xFFFFFFFF)
    return rng.choice(MOODS[bucket])


def _sorted_group(state: Dict[str, Any], group: str) -> List[str]:
    return sorted(
        state["standings"][group],
        key=lambda team_id: (
            -state["standings"][group][team_id]["pts"],
            -state["standings"][group][team_id]["gd"],
            -state["standings"][group][team_id]["gf"],
            -TEAM_BY_ID[team_id]["power"],
            team_id,
        ),
    )


def _refresh_dynamic_titles(state: Dict[str, Any]) -> None:
    net = _net_assets(state)
    if state["debt"] > 0:
        state["dynamic_title"] = "dog_end"
    elif net >= 120_000:
        state["dynamic_title"] = "analyst"
    elif net >= 100_000:
        state["dynamic_title"] = "steady"
    elif net >= 50_000:
        state["dynamic_title"] = "tuition"
    elif net >= 10_000:
        state["dynamic_title"] = "hupu_bro"
    elif net > 0:
        state["dynamic_title"] = "rooftop"
    else:
        state["dynamic_title"] = "dog_end"


def _add_title(state: Dict[str, Any], title: str) -> None:
    if title not in state["permanent_titles"]:
        state["permanent_titles"].append(title)


def _match_by_display_index(state: Dict[str, Any], raw: str) -> Optional[Dict[str, Any]]:
    try:
        index = int(raw)
    except ValueError:
        return None
    matches = state.get("current_matches", [])
    if index < 1 or index > len(matches):
        return None
    return matches[index - 1]


def _parse_amount(raw: str, allow_large: bool = False) -> Any:
    try:
        amount = int(raw)
    except ValueError:
        return "金额必须是整数。"
    if amount < MIN_BET and not allow_large:
        return f"单次下注最低 {MIN_BET}。小于这个数，庄家懒得开账本。"
    if amount <= 0:
        return "金额必须大于 0。"
    return amount


def _parse_goals_pick(raw: str) -> Optional[Tuple[str, int]]:
    match = re.match(r"^(over|under)(\d+)$", raw)
    if not match:
        return None
    line = int(match.group(2))
    if line < 1 or line > 12:
        return None
    return match.group(1), line


def _net_assets(state: Dict[str, Any]) -> int:
    return int(state["cash"] - state["debt"])


def _fair_odds(probability: float) -> float:
    return 1 / max(0.001, probability)


def _house_edge(amount: int, odds: float, fair_odds: float) -> float:
    return round(max(0.0, amount * (1 - odds / max(0.001, fair_odds))), 2)


def _house_edge_total(state: Dict[str, Any]) -> float:
    return round(sum(float(bet.get("house_edge", 0)) for bet in state.get("bets", [])), 2)


def _house_edge_line(state: Dict[str, Any]) -> str:
    return (
        f"\u5e84\u5bb6\u7d2f\u8ba1\u62bd\u6c34\uff1a{_house_edge_total(state):,.2f}"
        "\uff08\u8fd9\u662f\u65e0\u8bba\u4f60\u8f93\u8d62\u90fd\u6ce8\u5b9a\u4ea4\u7684\u7a0e\uff09"
    )


def _team_name(team_id: Optional[str]) -> str:
    if not team_id:
        return "-"
    return TEAM_BY_ID.get(team_id, {}).get("name", team_id)


def _poisson_pmf(k: int, lam: float) -> float:
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def _poisson_sample(rng: RNG, lam: float) -> int:
    limit = math.exp(-lam)
    product = 1.0
    k = 0
    while product > limit and k < 12:
        k += 1
        product *= rng.random()
    return max(0, k - 1)


def _odds(probability: float, margin: float, low: float, high: float, fluct: float) -> float:
    probability = max(0.001, probability)
    value = (1 / probability) * margin * fluct
    return round(_clamp(value, low, high), 2)


def _clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, value))


def _save_state(state: Dict[str, Any]) -> None:
    save_file = _save_file()
    save_file.parent.mkdir(parents=True, exist_ok=True)
    save_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_state() -> Optional[Dict[str, Any]]:
    save_file = _save_file()
    if not save_file.exists():
        return None
    return json.loads(save_file.read_text(encoding="utf-8"))


def _save_file() -> Path:
    configured = os.environ.get("GAMBLER_SAVE")
    return Path(configured).expanduser() if configured else SAVE_FILE


if __name__ == "__main__":
    print(OPENING_TEXT)
    print("输入 help 查看命令，输入 Ctrl+C 退出。")
    while True:
        try:
            user_command = input("> ")
        except (KeyboardInterrupt, EOFError):
            print("\n再见。现实里别赌，虚拟里也别太上头。")
            break
        print(cmd(user_command))
