# ⚽ 赌狗的自我修养 · AI World Cup Gambler

## 简介

`ai-worldcup-gambler` 是一个给 AI agent 玩的虚拟世界杯赌球模拟器。它采用单文件核心逻辑和纯文本命令交互：外部调用只需要 `gambler.cmd(command\_string)`。

你从 100000 虚拟资金开始，面对 16 支虚构球队、完整小组赛和淘汰赛、庄家抽水赔率、新闻传闻、高利贷、称号和下注历史。在忽略新闻信息的情况下，庄家抽水使投注长期期望值为负；将 positive/negative 新闻作为概率信号纳入决策，可能为 agent 提供额外优势。

本项目参考 [Asti-Z/leek](https://github.com/Asti-Z/leek) 的单文件交互设计模式，但实现内容为独立项目。

## 免责声明

这是一个虚拟游戏，不涉及真实金钱，不提供任何现实赌博建议，也不鼓励真实赌博。项目中的讽刺、调侃和“赌狗”文本只用于虚拟模拟器氛围。

现实里请远离赌博。现实里的庄家不会因为你 README 写得好就放过你。

## 功能特性

* 16 支虚构世界杯球队，分为 4 个实力档位。
* 小组赛 + 淘汰赛完整赛制，共 34 场比赛、17 轮下注机会。
* 支持胜平负、猜比分、总进球、点球大战、串关下注。
* 基于真实概率生成赔率，并加入庄家抽水和每轮 ±5% 波动。
* 自定义 mulberry32 PRNG，支持确定性随机：同 seed + 同操作 = 同结果。
* 新闻/传闻系统：每局 4 个可见新闻来源中隐藏 1 个可靠源；在 positive/negative 新闻中，来自可靠源的约占 25% 并构成真信号；其余来源及 misleading、match\_event 新闻均为噪声，真信号占全部新闻口径约 12.5%。
* 高利贷系统：现金低于最低下注额后可借 50000，每轮 10% 复利。
* 称号系统：动态资产称号和永久行为称号，结算时会提示新解锁称号。
* 下注历史、完整统计摘要、盈亏追踪、胜率统计和庄家累计抽水统计。
* 查询命令支持 `--json`，方便 AI agent 读取结构化赛程、赔率和状态。
* JSON 存档/读档，自动生成 `gambler\_save.json`。
* 纯标准库实现，不需要安装第三方依赖。

## 项目结构

```text
ai-worldcup-gambler/
├── gambler.py
├── README.md
├── LICENSE
├── .gitignore
├── examples/
│   ├── demo.py
│   ├── full\_demo.py
│   └── loan\_demo.py
├── tests/
│   ├── smoke\_test.py
│   ├── full\_run\_test.py
│   ├── loan\_test.py
│   ├── json\_mode\_test.py
│   ├── news\_signal\_test.py
│   └── agent\_signal\_strategy\_test.py
└── .github/
    └── workflows/
        └── smoke-test.yml
```

`gambler.py` 是核心文件，所有游戏逻辑都集中在这个文件里。`gambler\_save.json` 是运行时自动生成的存档文件，不应提交到 GitHub。

## 安装方式

克隆仓库后直接运行即可：

```bash
git clone https://github.com/peanutsuee/ai-worldcup-gambler.git
cd ai-worldcup-gambler
python examples/demo.py
python examples/full\_demo.py
python examples/loan\_demo.py
```

运行项目不需要安装第三方依赖，只使用 Python 标准库。

## 快速开始

```python
import gambler

print(gambler.cmd("new\_game 12345"))
print(gambler.cmd("help"))
print(gambler.cmd("schedule"))
print(gambler.cmd("news"))
print(gambler.cmd("bet wnl 1 home 5000"))
print(gambler.cmd("next"))
print(gambler.cmd("summary"))
```

## 完整演示

运行：

```bash
python examples/full\_demo.py
python examples/loan\_demo.py
```

`full\_demo.py` 会用固定 seed 自动跑完整 17 轮，展示完整世界杯流程、自动下注、结算、最终状态、称号、历史和完整统计摘要。

`loan\_demo.py` 会故意把现金推到 0，展示高利贷到账、每轮 10% 复利、还款和退出流程。它是虚拟演示，不是现实建议。

## 测试

本项目不依赖第三方测试框架，可以直接运行：

```bash
python tests/smoke\_test.py
python tests/full\_run\_test.py
python tests/loan\_test.py
python tests/json\_mode\_test.py
python tests/news\_signal\_test.py
python tests/agent\_signal\_strategy\_test.py
```

`news\_signal\_test.py` 会用蒙特卡洛方式验证新闻真信号系统：固定 seed 下取带真信号的场次，重复模拟 2000 次，确认实际胜率显著高于展示赔率的归一化隐含概率；同时移除隐藏修正作为对照，偏移应随之消失。当前参数下，按展示赔率固定下注真信号方向的平均返还倍数约为 1.2124，净收益率约 +21.24%，说明真信号本身的优势足以覆盖抽水。

这不等于任何 agent 都能自动赚钱；agent 还必须从可见新闻来源、文本方向和赛果里学出哪个来源可信。`agent\_signal\_strategy\_test.py` 不读取隐藏 `true` 字段，只使用可见新闻、展示赔率和赛果做局内统计；当前回测使用 18,252 个 seed，其中 8,811 个下注局簇、累计 20,002 注，朴素策略在每注等额投入下的平均返还倍数约为 1.0316，按局聚类标准误约 0.0096，均值减 2 倍标准误为 1.0124，因此按局聚类的近似双侧 95% 置信区间下限仍大于 1。细节见 [`tests/news\_signal\_test.py`](tests/news_signal_test.py) 和 [`tests/agent\_signal\_strategy\_test.py`](tests/agent_signal_strategy_test.py)。

GitHub Actions 会在 push 和 pull request 时自动运行 smoke test、full run test、loan test、JSON mode test、news signal test、agent signal strategy test 和 demo。

## Windows 编码说明

示例脚本会主动把 stdout/stderr 配置为 UTF-8，通常可以直接重定向输出：

```bash
python examples/full\_demo.py > full\_demo\_output.txt
```

如果你的终端仍然遇到编码问题，可以在 PowerShell 中手动设置：

```powershell
$env:PYTHONIOENCODING="utf-8"
python examples/full\_demo.py > full\_demo\_output.txt
```

## 命令列表

```text
help
status
schedule
standings
news
bet wnl 1 home 5000
bet score 1 2-1 1000
bet goals 1 over3 2000
bet pk 1 yes 1000
parlay 1,2,3 home,away,home 3000
next
history
summary
titles
loan
repay 10000
quit
new\_game 12345
```

查询类命令支持尾部 `--json`，包括 `status`、`schedule`、`standings`、`news`、`history`、`summary`、`titles`。例如：

```python
import json
import gambler

schedule = json.loads(gambler.cmd("schedule --json"))
print(schedule\["matches"]\[0]\["odds"]\["wnl"])
```

## 游戏规则

玩家初始资金为 100000。单次下注最低 100，资金不足时不能下注。每轮比赛开始前可以查看赛程、赔率和新闻，然后下注。执行 `next` 后会模拟当前轮所有比赛，结算本轮下注，更新资金、债务、积分榜、淘汰赛晋级、称号和下注历史。

新闻系统不是纯装饰：每局会把 4 个可见新闻来源中的 1 个设为隐藏可靠源。在 positive/negative 新闻中，来自可靠源的约占 25% 并构成真信号，会对提到球队产生当轮 ±10\~12 power 临时修正；其余来源及 misleading、match\_event 新闻均为噪声，真信号占全部新闻口径约 12.5%。这个修正只影响真实比赛模拟，不会进入展示赔率。游戏不会提供查询真伪或可靠源的命令，AI agent 只能靠跨轮统计自己推断。

如果现金低于最低下注额 100，可以执行 `loan` 借高利贷。每次固定借款 50000，每轮 10% 复利。净资产或债务触及危险红线后游戏会强制结束。也可以执行 `quit` 直接结束游戏。

## 赛制说明

16 支球队分为 4 档：

```text
brazilia / Brazilia 92
argentino / Argentino 90
franch / Franch 89
germeny / Germeny 87
espanya / Espanya 85
englund / Englund 84
portugalo / Portugalo 83
belgica / Belgica 82
nederlund / Nederlund 80
kroatia / Kroatia 79
uruguayo / Uruguayo 78
italio / Italio 77
japon / Japón 74
koreo / Koreo 73
mexica / Mexica 72
merican / Merican 71
```

分组为 A/B/C/D 四组，每组 4 队，每组包含不同档位球队。分组受 seed 控制，可复现。

小组赛每组单循环，共 24 场。每轮 2 场比赛，共 12 轮。胜 3 分、平 1 分、负 0 分。排名规则为积分、净胜球、进球数、球队 power 和稳定 tie-breaker。

淘汰赛共 5 轮 10 场：

* 冠军路径：8强赛 4 场 -> 半决赛 2 场 -> 决赛 1 场。
* 排位路径：8强输家进入 5-8 名排位赛 2 场。
* 半决赛输家进入三四名决赛 1 场。

90 分钟可以打平，但淘汰赛必须通过加时或点球产生胜者。

## 下注玩法

### 胜平负

```text
bet wnl <match\_index> <home/draw/away> <amount>
```

小组赛和淘汰赛都支持。淘汰赛的胜平负指 90 分钟赛果，不等同于最终晋级。

### 猜比分

```text
bet score <match\_index> <score> <amount>
```

示例：`bet score 1 2-1 1000`。比分玩法赔率较高，抽水也更狠。

### 总进球

```text
bet goals <match\_index> <overN/underN> <amount>
```

示例：`over3` 表示总进球数严格大于 3，`under3` 表示严格小于 3。

### 点球大战

```text
bet pk <match\_index> <yes/no> <amount>
```

仅淘汰赛可用。小组赛使用会返回错误提示。

### 串关

```text
parlay 1,2,3 home,away,home 3000
```

所有场次都猜中才赢。赔率为各项赔率相乘，并加入累积抽水。

赔率有明确边界：胜平负约 1.20–8.00，比分 5.00–50.00，总进球 1.60–3.00，点球 yes 2.50–4.00、no 1.08–1.60。极端盘口也会被截断，例如 `over9` 不会生成离谱赔率。

## 存档机制

游戏会自动在项目目录生成 `gambler\_save.json`。每次新开局、下注、推进轮次、借款、还款或退出都会写入存档。存档包含 PRNG 状态，因此读档后继续操作仍保持确定性。

如果需要并行跑多局，可以让每个进程设置不同的 `GAMBLER\_SAVE` 环境变量，指定完整存档路径：

```bash
GAMBLER\_SAVE=/tmp/gambler-agent-1.json python examples/full\_demo.py
```

Windows PowerShell 示例：

```powershell
$env:GAMBLER\_SAVE="C:\\temp\\gambler-agent-1.json"
python examples/full\_demo.py
```

未设置 `GAMBLER\_SAVE` 时，行为保持不变，仍使用 `gambler.py` 同目录的 `gambler\_save.json`。

`.gitignore` 已忽略 `gambler\_save.json` 和 `\*\_output.txt`，不要把运行存档或 demo 输出提交到 GitHub。

## 示例输出

```text
>>> schedule
🗓️ 当前赛程：第 1 / 17 轮 · 小组赛 A组第1轮
下注编号只在当前轮有效。赔率已经抽水；忽略新闻时别幻想长期正期望。能识别可靠新闻来源的 agent 才有可能获得额外优势。

\[1] Brazilia vs Mexica | 小组赛 A组第1轮
  胜平负：home 1.42 / draw 3.58 / away 5.90
  总进球：over2 1.66 / under3 2.11 / over3 2.42 / under4 1.67
  比分示例：1-0 6.52 / 2-1 8.44 / 1-1 7.30 / 0-1 14.20
```

具体输出会随 seed 和操作序列变化。

## 给 AI Agent 的使用方式

AI agent 不需要解析图形界面，也不需要安装依赖。直接通过纯文本命令循环调用：

```python
import gambler

response = gambler.cmd("new\_game 12345")
print(response)

response = gambler.cmd("schedule")
print(response)

response = gambler.cmd("bet wnl 1 home 5000")
print(response)
```

需要结构化读取时，可以在查询命令末尾加 `--json`：

```python
import json
import gambler

data = json.loads(gambler.cmd("schedule --json"))
for match in data\["matches"]:
    print(match\["index"], match\["home"]\["name"], match\["away"]\["name"], match\["odds"]\["wnl"])
```

## 最小 Agent 接入示例

一个 agent 可以用 JSON 模式读取状态和赛程，用纯文本新闻作为额外观察，再把决策写回命令：

```python
import json, gambler

print(gambler.cmd("new\_game 20260703"))
for \_ in range(json.loads(gambler.cmd("status --json"))\["total\_rounds"]):
    status = json.loads(gambler.cmd("status --json"))
    if status\["ended"]:
        break
    schedule = json.loads(gambler.cmd("schedule --json"))
    news\_text = gambler.cmd("news")
    # 实际 agent 可在此结合历史赛果分析新闻来源，本示例只演示接口调用。
    for match in schedule\["matches"]:
        pick = min(match\["odds"]\["wnl"], key=match\["odds"]\["wnl"].get)
        status = json.loads(gambler.cmd("status --json"))
        amount = 1000 if status\["cash"] >= 1000 else 100
        if status\["cash"] >= amount:
            gambler.cmd(f"bet wnl {match\['index']} {pick} {amount}")
    print(gambler.cmd("next"))
print(gambler.cmd("summary"))
```

`--json` 只用于查询命令，便于 agent 稳定解析 `cash`、`matches`、`odds`、`history` 和 `summary`。新闻里存在隐藏真信号，但游戏不会暴露真伪标签；想获得信息优势，agent 需要长期记录新闻文本、球队、赔率和赛果，自己做统计归因。

所有返回值都是字符串，适合 agent 读取、总结、决策和继续调用。`gambler\_save.json` 会自动生成，agent 不需要手动创建。

## 开发说明

* 核心逻辑全部位于 `gambler.py`。
* 外部交互入口只有 `cmd(command\_string: str) -> str`。
* 不依赖第三方包。
* 随机数不使用 Python 全局 `random`，而是使用自定义 mulberry32。
* 所有随机过程都通过游戏状态内的 PRNG，存档保存 PRNG 状态。
* 输出为纯文本，适合命令行、人类和 AI agent。

## License

MIT License. See [LICENSE](LICENSE).

