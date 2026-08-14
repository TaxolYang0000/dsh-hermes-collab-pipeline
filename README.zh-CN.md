# DSH ↔ Hermes 双 Agent 协作管道

> **English README: [README.md](README.md)**

> ⚠️ **AI 生成代码声明**：本仓库所有代码均由 DeepSeek 模型生成，**未经人工审查**。使用风险自负；部署前请人工审查关键路径（安全、权限、文件操作）。

> 📋 **许可证与借鉴声明**：MIT。代码改编自 DeepSeek Harness、Hermes Agent、dsh-harness-mcp-server（均为 MIT）——详见 [NOTICE-借鉴与合规.md](NOTICE-借鉴与合规.md)。同领域相关项目：[Ericwong5021/dsh-kanban](https://github.com/Ericwong5021/dsh-kanban)（同名不同类型：React UI 看板 vs 我们的后台执行插件）。

让 **Hermes Agent**（交互式 AI agent）和 **DSH / DeepSeek Harness**（Web 端 AI agent）
像两个同事一样协作：Hermes 负责下发任务、审核结果；DSH 在 Web GUI 里自动执行、
回写看板、通知完成。全程无人值守，你只需要看结果。

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

## 快速开始

> 📖 **新人从零安装请看 [INSTALL-安装指南.md](INSTALL-安装指南.md)**（含 kanban 初始化、插件挂载、技能部署、验证步骤、已知坑）
>
> 🤖 **AI Agent 用户（如另一个 Hermes/DSH/Claude Code 实例）**：直接运行
> `./install.sh --yes`（全自动、幂等、可重跑）。脚本会自动探测路径、跳过已完成的步骤、
> 前置条件不满足时 exit 2 并给出修复提示。要预演先跑 `./install.sh --dry-run`。
> 首次运行前确保已初始化 DSH web profile（`dsh web --port 3080` 启动一次）。

前置条件：本机已装 Hermes Agent + DSH（npm 全局 @deepseek-ai/dsh），共享 ~/.dsh 目录。

```bash
# 0. 先 clone 本仓库（推送到 GitHub 后替换 URL）
git clone <你的仓库地址> && cd <仓库目录>

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
# 带模型下发（DSH 用 pro 执行重任务）
/dsh-send --model deepseek-v4-pro 写一个爬虫抓取 HLTV 数据

# 带技能下发（把 Hermes skill 复制到共享区给 DSH 参考）
/dsh-send --skill two-step-t1-dip-buy-strategy 用这个策略分析当前行情

# 指定工作目录
/dsh-send --workspace dir:$DSH_WORKSPACE/weekly-reports 写本周周报

# 查看队列
/inbox
```

## 设计原则（双 Agent 评审门）

- **属地分工**：谁的环境谁是主体——DSH 相关归 DSH 写、Hermes 相关归 Hermes 写，
  实现方产出后另一 agent 独立审查（安全/错误处理/作用域/依赖兼容）
- **互重启**：Hermes 重启由 DSH 执行、DSH 重启由 Hermes 执行；
  重启对方进程的任务不得进看板自执行（watcher 跑在 DSH host 里，kill host=杀执行者）
- **落点白名单**：Hermes 侧是唯一事实源，DSH watcher 权限预设镜像同一白名单
- **用户是最终合并批准人**：审查意见逐条回应（修复或说明为何不改），用户拍板

## 已知限制

- watcher **串行执行**任务（同一时刻只跑一个，后续排队）
- 10s 轮询 + fs.watch：准实时，不是实时
- SQLite 多进程写有锁竞争（busy_timeout + 重试兜底）
- 外部事件注入只作用于 Hermes CLI 会话，gateway 平台不走这条链路
- 插件代码更新后必须重启 dsh web 才生效（node 不热重载）

（fs.watch 事件合并/丢失时，watcher 兜底 30s 轮询。）

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

- `INSTALL-安装指南.md` — 从零安装完整步骤 + 已知坑
- `dsh-side/docs/DSH-Hermes双Agent协作管道-能力盘点与可行性.md` — 项目缘起（DSH 能力盘点 + 协作可行性分析）
- `dsh-side/plugins/dsh-kanban-watcher/README.md` — watcher 插件详细文档（配置/使用/安全）
- `hermes-side/PR-提交说明.md` — 给 Hermes Agent 提 issue 的材料
