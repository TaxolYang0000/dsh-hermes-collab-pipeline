# Agent Federation Platform

> 自带宿主 agent，我们提供联邦机制。

> **English README: [README.md](README.md)**

> ⚠️ **AI 生成代码声明**：本仓库所有代码均由 DeepSeek 模型生成，**未经人工审查**。使用风险自负；部署前请人工审查关键路径（安全、权限、文件操作）。

> ⚠️ **内核补丁提醒（安装前必读）**：仓库里有一个可选组件——`hermes-side/hermes-external-event-steer.patch`——它修改 **Hermes 核心源码**（`cli.py` + `hermes_cli/config_defaults.py`），用于增加"CLI 自动弹出【外部通知】"这个增强。该补丁 **可选且默认关闭**：
> - **不打补丁，核心管道 100% 正常**（任务下发 → DSH 执行 → 结果回写看板）。只是需要用 `hermes kanban --board dsh show <id>` 手动查看结果，而不是自动弹出。
> - 补丁**依赖 Hermes 版本**：针对特定版本编写。如果 `git apply` 失败（版本差异），跳过即可——管道照常工作，只少了自动弹出。
> - `install.sh` 在补丁无法应用时**不会失败**——它会警告并继续。
> - 详见下方「什么需要内核补丁？」。

> 📋 **许可证与借鉴声明**：MIT。代码改编自 DeepSeek Harness、Hermes Agent、dsh-harness-mcp-server（均为 MIT）——详见 [NOTICE-借鉴与合规.md](NOTICE-借鉴与合规.md)。同领域相关项目：[Ericwong5021/dsh-kanban](https://github.com/Ericwong5021/dsh-kanban)（同名不同类型：React UI 看板 vs 我们的后台执行插件）。

本仓库当前实现的是双 agent 管道（Hermes 编排、DSH 经 kanban 队列执行），并走向 agent 联邦：任意 AI 编码 agent 通过同一队列接入，交叉审查彼此产出，通过分级辩论协议审议——由你作为最终决策者。

## 动机

一个 agent 独立干活，能力边界就是模型边界。偏见没人纠正，盲区没人填补，问题再复杂也只能自己硬想。多 agent 协作的价值就在这里：异构的 agent 互相审查，能纠正单 agent 的自证偏差（MAD 论文已验证）。

这个项目现在的形态是 Hermes 和 DSH 两个 agent 协作。Hermes 把任务写进 kanban 队列，DSH 在 Web GUI 里认领执行，结果回写看板，完成后通知 Hermes。整条链路已经实测验证：任务状态机可靠（认领有锁，同一个任务不会被两个 agent 重复执行；崩溃后任务能恢复）、全程无人值守（触发文件事件驱动加权限预设）、执行会话可回看、完成自动通知、跨任务会话继承、基础交叉审查（实现方产出，另一方独立审）。

但这条管道有两个没解决的问题：

1. 执行锁死在单一 agent 类型。想加 Codex 就得再写一个 watcher，每加一个 agent 成本线性增长。
2. 没有协商通道。看板评论是异步留言，不是结构化的轮次审议，意见没法迭代、没法收敛。

还有一个原理性的天花板：双板互审的虚假共识。

精密机加工中，标准平面的制作采用刮研工艺。两块平板互研，永远得不到高精度平面：如果一块凸、一块凹，它们互研会完美贴合，但两块都不是平面，误差被互相适应了。三块平板闭环互研（A对B、B对C、C对A）才行：任何一块的凸起都会被另外两块暴露，三轮循环下来三块都逼近真平面。

双 agent 互审就是双板互研。Hermes 审 DSH、DSH 审 Hermes，两个 agent 可以互相认可彼此的盲区，达成一个"一致但都错"的结论——它们不是找到了正确答案，是互相适应了错误。要破除虚假共识，需要闭环：至少三方循环互审（A审B、B审C、C审A），任何单点的错误都会被与它不互补的第三方抓住。

这就是联邦的深层理由。不是多一个 agent 干活，是闭环互审让"一致"必须经过三方验证，误差无处藏。异构（跨模型系）降低同源盲区的概率，闭环（三方循环）消除虚假共识的自由度——两个都要，闭环是本质。

类似的思路别人也在做，验证了方向可行：

- win4r/team-tasks：辩论模式（round → collect → cross-review → synthesize）和我们要做的审议协议几乎一样，证明协议可落地。
- Skytliang/Multi-Agents-Debate (MAD)：论文证明多 agent 辩论能纠正单 agent 的偏见、僵化和盲区，证明动机成立。
- thunlp/ChatEval：多 agent 辩论用于 LLM 评估，同源佐证。
- omnigent-ai/omnigent：meta-harness，一个会话里混排 Claude Code、Codex、Cursor、Hermes，让一个 agent 审查另一个的产出，证明任意混排可行。
- Detrol/quorum-cli：多模型辩论 CLI，七种讨论方法，证明辩论交互已经产品化。
- majiayu000/harness：Rust 控制平面，带策略和审查的 Claude Code/Codex 编队，证明审查层可以工程化。
- Happenmass/omux：基于 tmux 的并行 CLI 编码 agent 编排，证明并行执行可以无人值守。

但它们没有一个同时具备我们认为核心的三样东西：带硬状态机的持久化队列（kanban）、刻意异构的执行（跨模型配对）、人类把关的最终决策。别人的协议我们借鉴，记录面我们自己搭。这就是这个仓库存在的理由。

本动机的完整论证详见文章：**[Coding Agent 的下一步要怎么走——为什么我们需要一个多agent讨论架构](docs/coding-agent-下一步要怎么走.md)**（原始版本为中文；英文版：[Where Should Coding Agent Go Next?](docs/coding-agent-whats-next.md)）。文章完整展开本文动机、批判自身假设，并给出该架构真正成立的适用条件。

## 综述

Agent Federation Platform 是通用多智能体协作层。它通过共享 kanban 队列联邦任意 AI 编码 agent，让它们交叉审查彼此产出，并对高风险决策运行分级多智能体辩论，始终由人类把关。平台与编排者无关：自带宿主 agent（参考部署使用 Hermes），平台提供联邦机制。

核心能力：

- 共享队列：kanban 任务状态机，认领有锁、崩溃可恢复、审计完整。
- 交叉审查：实现方产出，另一方独立审，强制实现与审查分离。
- 分级辩论：直接执行、双模型互审、全量辩论三级，按任务价值启用。
- 人类终审：任何统一建议都只是建议，确认后才执行。

## 适合什么情况

- 你有 **Hermes Agent** 和 **DSH（DeepSeek Harness）** 两个 AI agent 在**同一台机器**上
- 想让 DSH 的 Web GUI 会话自动执行 Hermes 下发的任务（而不是每次手动去 GUI 里开对话）
- 想要一个**任务队列**：Hermes 把任务写进 kanban 看板，DSH watcher 认领并串行执行
- 想要**完成通知**：DSH 做完任务自动弹到 Hermes 会话里，不用轮询

不适合：单 agent 场景（只有一个 agent 就用不上协作管道）、
跨机器分布式场景（本方案假设同一台机器、共享文件系统）。

## 架构

```
┌─────────────┐    kanban 看板 (SQLite)   ┌──────────────────┐
│   Hermes    │  ──────────────────────→  │   DSH Web GUI    │
│  (CLI/飞书) │  hermes kanban create     │  (dsh web :3080) │
└─────┬───────┘                           └────────┬─────────┘
      │  /dsh-send 技能                              │  watcher 插件
      │                                            │  认领 → 执行 → 回写
      │  ~/.dsh/kanban-trigger/<id>.trigger         │
      └─────────────────────── 事件驱动唤醒 ─────────┘
                                                  │
      ~/.dsh/kanban-done/<id>.done  ←─────────────┘  writeDoneFile()
      │
      ▼
  Hermes 空闲循环 _drain_done_notifications
      → 会话自动弹出【外部通知】任务已完成
```

四个关键机制：

1. **看板队列**：任务状态机（ready → running → done/blocked），SQLite 持久化，崩溃可恢复
2. **事件驱动唤醒**：Hermes 写 trigger 文件，watcher 的 fs.watch 立即响应（+30s 兜底轮询）
3. **落点白名单**：输出只允许写到白名单目录（默认 $DSH_WORKSPACE、桌面），防越权写
4. **完成通知**：watcher 写 done 文件 → Hermes 会话自动感知，无需轮询

## 仓库结构

```
├── dsh-side/          DSH 侧组件（DSH 维护）
│   ├── plugins/dsh-kanban-watcher/   看板 watcher 插件源码 + README
│   ├── hermes-side/                  Hermes 侧技能源码（dsh-send SKILL.md）— 与 hermes-side/dsh-send-skill/ 互为镜像
│   ├── docs/                          能力盘点与协作可行性
│   └── scripts/                       会话解压/提取/注释改进工具 + 重启脚本
└── hermes-side/      Hermes 侧改动（Hermes 维护）
    ├── hermes-external-event-steer.patch   源码 diff（104 行）
    ├── dsh-send-skill/                /dsh-send 技能 — 与 dsh-side/hermes-side/dsh-send/ 互为镜像
    ├── dsh-web.service                systemd 服务文件（模板——使用前编辑占位符）
    ├── PR-提交说明.md                 提 Hermes issue 用的材料
    └── README.md                      用法说明
```

## 什么需要内核补丁？

| 能力 | 需要内核补丁？ | 不打补丁怎么工作 |
|---|---|---|
| 给 DSH 下发任务（`/dsh-send`） | ❌ 不需要 | 纯 Hermes 技能 + kanban CLI——始终可用 |
| DSH 在 Web GUI 执行、回写看板 | ❌ 不需要 | watcher 插件做的——始终可用 |
| 查看结果（`hermes kanban --board dsh show <id>`、`/inbox`） | ❌ 不需要 | 看板评论——始终可用 |
| DSH 写 done 文件（`~/.dsh/kanban-done/`） | ❌ 不需要 | watcher 插件功能——始终可用 |
| **Hermes CLI 完成时自动弹出【外部通知】** | ✅ **需要** | 手动查看板代替 |

**结论**：内核补丁只加了最后一行（自动弹出）。其他都是插件/技能/配置层，任何 Hermes 版本都可用。跳过补丁只失去自动弹出，其他不受影响。

## 快速开始

> 📖 **新人从零安装请看 [INSTALL-安装指南.md](INSTALL-安装指南.md)**（含 kanban 初始化、插件挂载、技能部署、验证步骤、已知坑）
>
> 🤖 **AI Agent 用户（如另一个 Hermes/DSH/Claude Code 实例）**：直接运行
> `./install.sh --yes`（全自动、幂等、可重跑）。脚本会自动探测路径、跳过已完成的步骤、
> 前置条件不满足时 exit 2 并给出修复提示。要预演先跑 `./install.sh --dry-run`。
> 首次运行前确保已初始化 DSH web profile（`dsh web --port 3080` 启动一次）。

前置条件：本机已装 Hermes Agent + DSH（npm 全局 @deepseek-ai/dsh），共享 ~/.dsh 目录。

```bash
# 0. 先 clone 本仓库（--recurse-submodules 会拉取 dsh-kanban-watcher 插件子模块）
git clone --recurse-submodules <你的仓库地址> && cd <仓库目录>

# 1. DSH 侧：安装 watcher 插件 + 启动 web
cd ~/.dsh/profiles/web
pnpm add file:<仓库目录>/dsh-side/plugins/dsh-kanban-watcher
systemctl --user enable --now dsh-web.service   # 或手动: dsh web --port 3080
# （dsh-web.service 是模板——先编辑 <DSH_BIN>/<NPM_PREFIX> 占位符）

# 2. Hermes 侧：应用 patch + 开配置
cd ~/.hermes/hermes-agent
git apply <仓库目录>/hermes-side/hermes-external-event-steer.patch
hermes config set features.external_event_steer true
# 重启 Hermes CLI

# 3. 下发任务
# 在 Hermes 会话里：
/dsh-send 帮我分析本周交易数据，输出报告到 DSH 工作区

# 4. 完成通知自动弹出
# 【外部通知】任务 t_xxxx「帮我分析本周交易数据」已完成。结果摘要：...
```

## 使用示例

```bash
# 带模型下发（注意：插件 modelMap 只映射 flash + __fallback__，
# 指定 modelMap 里没有的模型（如 pro）会 fallback 到 flash 执行）
/dsh-send --model deepseek-v4-flash 写一个爬虫抓取 HLTV 数据

# 带技能下发（把 Hermes skill 复制到共享区给 DSH 参考）
/dsh-send --skill two-step-t1-dip-buy-strategy 用这个策略分析当前行情

# 会话继承（续接之前对话的上下文，v0.2.0 新功能）
/dsh-send --resume 继续讨论X 再分析一下刚才的结论

# 指定工作目录
/dsh-send --workspace dir:$DSH_WORKSPACE/weekly-reports 写本周周报

# 查看队列
/inbox
```

## 设计原则（跨 agent 评审门）

- **属地分工**：谁的环境谁是主体——DSH 相关归 DSH 写、Hermes 相关归 Hermes 写，
  实现方产出后另一 agent 独立审查（安全/错误处理/作用域/依赖兼容）
- **互重启**：Hermes 重启由 DSH 执行、DSH 重启由 Hermes 执行；
  重启对方进程的任务不得进看板自执行（watcher 跑在 DSH host 里，kill host=杀执行者）
- **落点白名单**：Hermes 侧是唯一事实源，DSH watcher 权限预设镜像同一白名单
- **用户是最终合并批准人**：审查意见逐条回应（修复或说明为何不改），用户拍板

## 已知限制

- watcher **串行执行**任务（同一时刻只跑一个，后续排队）
- 30s 兜底轮询 + fs.watch：准实时，不是实时
- SQLite 多进程写有锁竞争（busy_timeout + 重试兜底）
- 外部事件注入只作用于 Hermes CLI 会话，gateway 平台不走这条链路
- 插件代码更新后必须重启 dsh web 才生效（node 不热重载）

（fs.watch 事件合并/丢失时，watcher 兜底 30s 轮询。）

## 为什么不用现成的方案

- **社区 MCP server（dsh-harness-mcp-server）不采用**：其依赖 `^0.0.1-rc.1` 与 DSH
  profile `0.1.0-rc.6` semver 不匹配（装上有单例冲突风险）、任务队列纯内存（重启即丢）、
  会话按 cwd 复用（非每任务新对话）。本项目的 kanban 看板是持久化队列，正好补这些短板。
- **过渡性定位**：本管道预期寿命 = DSH 官方 ACP/JSON-RPC 完善前（入口与执行解耦）。
  如果 DSH 官方提供更成熟的跨 Agent 任务协议，可替换 watcher 而保留看板与技能层。
- **部署注意**：Hermes gateway 自带 kanban watcher，勿在 board `dsh` 上启用 Hermes
  dispatcher（会与 DSH watcher 抢任务）。本项目的 board/assignee 隔离设计已避免冲突。

## 路径变量说明

仓库中的代码和文档经过脱敏处理，本机真实路径以 `$VAR` 占位符表示。部署时按你的环境替换：

| 变量 | 含义 | 示例 |
|------|------|------|
| `$HOME` / `$USER` | 用户主目录 / 用户名 | `/home/alice` / `alice` |
| `$DSH_WORKSPACE` | DSH 工作区（任务默认目录） | `/home/alice/DSH` |
| `$DSH_HOME` | DSH 数据目录 | `~/.dsh` |
| `$DSH_TRIGGER_DIR` | 看板触发文件目录 | `~/.dsh/kanban-trigger` |
| `$DSH_DONE_DIR` | done 文件目录（完成通知） | `~/.dsh/kanban-done` |
| `$DSH_SESSIONS` | DSH 会话存档目录 | `~/.dsh/sessions` |
| `$DSH_WEB_PROFILE` | DSH web profile 目录 | `~/.dsh/profiles/web` |
| `$DSH_BIN` | dsh 可执行文件 | `/home/alice/.hermes/node/bin/dsh` |
| `$HERMES_HOME` | Hermes 数据/源码目录 | `~/.hermes` |
| `$HERMES_BIN` | hermes CLI 可执行文件 | `~/.local/bin/hermes` |
| `$HERMES_BIN_DIR` | hermes CLI 所在目录 | `~/.local/bin` |
| `$NPM_PREFIX` | npm 全局前缀 | `~/.hermes/node` |
| `$HERMES_VENV_PYTHON` | Hermes venv Python | `~/.hermes/hermes-agent/venv/bin/python` |
| `$DESKTOP` | Windows 桌面 | `/mnt/c/Users/xxx/Desktop` |
| `$WIN_USERNAME` | Windows 用户名 | `alice` |
| `$HOSTNAME` | 机器主机名 | `myhost` |

## 相关文档

- `CHANGELOG.md` — 更新日志（版本历史 + 新内容）
- `INSTALL-安装指南.md` — 从零安装完整步骤 + 已知坑
- `dsh-side/docs/DSH-Hermes双Agent协作管道-能力盘点与可行性.md` — 项目缘起（DSH 能力盘点 + 协作可行性分析）
- `dsh-side/plugins/dsh-kanban-watcher/README.md` — watcher 插件详细文档（配置/使用/安全）
- `hermes-side/README.md` — external_event_steer 原理与安全设计（done 文件不可信输入、seen baseline）
- `hermes-side/PR-提交说明.md` — 给 Hermes Agent 提 issue 的材料

## 展望

从双 agent 管道到完整联邦的路线图：

- P0 通用 driver。把 dsh-kanban-watcher 重构为 driver 接口（认领→执行→回写），任意 agent 通过一个 driver 文件接入（DSH、Codex、Claude Code、自定义）。
- P1 kanban 辩论状态机。round → collect → cross-review → synthesize，借鉴 win4r/team-tasks 的 debate 模式。
- P2 分级审议。直接执行 / 双模型互审 / 全量辩论，按任务价值启用；模型路由加 driver 注册表。
- P3 看板可视化面板。在 DSH Web GUI 中展示任务状态、模型、耗时、依赖与辩论轮次。
