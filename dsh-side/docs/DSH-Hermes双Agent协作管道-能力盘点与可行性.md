# DSH-Hermes 双 Agent 协作管道 · 能力盘点与可行性

> 来源：DSH 历史会话存档 `~/.dsh/sessions/<workspace-dir>/<session-id>/session.jsonl.zstd`
> （zstd 拼接帧，按帧边界逐帧解压后拼接，共 12179 帧 → 16060 行 JSONL）
> 会话时间：2026-08-14 17:19 ~ 17:27（Asia/Shanghai）
> 模型：`deepseek-official/deepseek-v4-flash`（reasoningEffort=high）
> 会话 profile：`web`（DSH Web GUI，http://127.0.0.1:3080）
> 本文档提取该会话第 1~3 轮完整内容并结构化整理；工具调用/结果已精简，最终结论为原文。

---

## 第 1 轮 · DSH 插件能力盘点（17:19:22 — 17:20:12）

### 1.1 用户提问

> 扫一下你现在有的插件，大致分个类，告诉我你能干什么

### 1.2 扫描结论：当前会话的插件组成

DSH 里的「插件」= 带 `dsh.bundle` 声明的 **profile bundle**，通过 `dsh plugin --profile <name> add <包名>` 安装，装于 `~/.dsh/profiles/<name>/node_modules/`。当前会话跑在 **web profile**，由两层 bundle 合成（均为 **v0.1.0-rc.6**）：

| 插件层 | 说明 |
|---|---|
| `@deepseek-ai/dsh-base` | **共享核心**：约 90 个插件行（会话、Agent 循环、全部工具、沙箱），所有 profile 共有 |
| `@deepseek-ai/dsh-web-app` | **浏览器界面层**：约 50 个插件行（Web 服务器、前端 UI、工作区/存储），仅 web profile |

> 结论：profile 的 `dependencies` 为空，**未安装任何第三方插件**。要扩展能力（如 MCP 客户端）用 `dsh plugin --profile web add <包名>`。核心层已内置 MCP 客户端库（`dsh-mcp-client`），只是当前 web profile 未接线（见第 2 轮）。

### 1.3 能力六大分类（最终回答原文整理）

#### ① 我直接使用的工具（本会话已挂载）

| 能力 | 工具 | 底层插件 |
|---|---|---|
| 文件读写/检索 | `read` / `write` / `edit` / `glob` / `grep` | `dsh-tool-fs`、`dsh-tool-fs-search`、`dsh-tool-str-replace-editor` |
| 执行 Shell | `bash`（含后台任务 `job_*`） | `dsh-tool-bash`、`dsh-tool-jobs`、`dsh-jobs-local` |
| 联网检索 | `web_search` | `dsh-tool-web` + `dsh-web-search-deepseek` |
| 委派协作 | `subagent` / `subagent_fork` / `workflow`（多子代理编排） | `dsh-tool-subagent*`、`dsh-tool-workflow`、`dsh-workflow-worker-thread` |
| 目标与规划 | `create_goal` / `update_goal`、`todo_write`、`plan-mode`、Ralph 新鲜代理循环 | `dsh-tool-goal`、`dsh-tool-todo`、`dsh-tool-ralph` |
| 交互与技能 | `ask_user_question`、`skill`（技能加载）、`read_image`（附件） | `dsh-tool-ask-user`、`dsh-tool-skill`、`dsh-attachment-local` |

#### ② Agent 核心循环

- 主循环与指令：`agent`、`agent-loop`、`agent-instructions`、`system-prompt`、`agent-default-model`（默认 deepseek-v4-flash）
- 上下文管理：`compaction-basic`（会话压缩）、`token-meter`、`timeout-policy`、`repeat-tool-reminder`、`tool-result-pruner`（工具结果裁剪）
- 模型接入：`llm` / `llm-deepseek` / `llm-pi-ai`（多供应商孪生）/ `llm-retry` / `credentials` / `settings`

#### ③ 会话与记忆

- JSONL 追加式持久化（`session-persistence-jsonl`）、标题自动生成（`session-title` / `session-title-llm`）
- SQLite 全文检索（`session-query-sqlite`，当前内存模式）、会话投影缓存（`session-projection` / `session-projection-cache`）、会话统计（`session-stats`）
- OTel 遥测（`session-telemetry-otel`）、图片附件存储（`attachment-local`，内容寻址，不入日志）

#### ④ 安全与沙箱

- 文件沙箱 + 观察策略（`fs-sandbox`、`fs-observation-policy`）
- Shell 沙箱（`bash-sandbox`、`pwsh-sandbox`）
- 审批流（`approval`、`user-approval`、权限预设 `permission` / `sandbox-policy`）
- 溢出策略（`spill-policy`，长输出落盘）

#### ⑤ Web 界面层（就是用户正在用的 GUI）

- 服务端：`webserver` / `web-runtime` / `web-startup` / `api-gateway` / 前端静态托管
- 全套 UI 模块：会话（`ui-conversation`）、工具调用轨迹（`ui-tool`、`ui-trajectory`）、子代理（`ui-subagent`）、任务（`ui-jobs`）、目标（`ui-goal`）、工作流运行（`ui-workflow-run`）、计划模式（`ui-plan`）、模型选择（`ui-model-selection`）、设置（`ui-settings*`）、插件清单（`ui-settings-plugin-inventory`）、工作区（`ui-workspace`）、目录选择器、消息反馈等

#### ⑥ 其他基础设施

- 定时器（`timer`）、HMR 热重载（`hmr`、`client-hmr`）
- 子进程/代码运行时（`subprocess`、`code-runtime`、worker thread）、存储域（`storage-json`、`storage-domain`）
- 会话导出、目录选择器、消息反馈、状态/用量统计等

### 1.4 一句话总结（原文）

> 我现在是一个带**文件读写 + Shell + 网页搜索 + 多子代理/工作流编排 + 长目标持久化 + 完整 Web 图形界面**的编码型 Agent；沙箱按需放行、审批需你确认，默认模型是 deepseek-v4-flash。目前 profile 里没有额外安装第三方插件，要扩展能力可以用 `dsh plugin --profile web add <包名>` 安装。

### 1.5 附录：两层 bundle 的完整插件清单（扫描原始输出）

**dsh-base（核心层，约 90 行）：**

```
timer hmr llm session typert typert-loader typert-gateway session-title session-title-llm
user-questions agent agent-default-model jobs llm-retry settings credentials llm-pi-ai
session-persistence-jsonl attachment-local session-query-sqlite session-projection
session-telemetry-otel subprocess sandbox sandbox-policy bash-sandbox pwsh-sandbox approval
permission shell-env tool-bash tool-pwsh tool-jobs fs-observation-policy tool-fs tool-fs-search
agent-instructions skill skill-filesystem skill-badge tool-skill commands command-feedback
goal goal-round-driver command-goal plan-mode token-meter compaction-basic command-compact
subagent subagent-spawn-in-process subagent-fork-in-process tool-subagent-control
tool-subagent-list-agents tool-subagent tool-subagent-fork tool-subagent-report
workflow-worker-thread tool-workflow timeout-policy spill-local spill-policy
session-checkpoint-policy tool-result-pruner tool-todo tool-goal tool-ralph
tool-str-replace-editor repeat-tool-reminder web web-search-deepseek tool-web tools
system-prompt agent-loop fs-sandbox llm-deepseek
```

**dsh-web-app（界面层，约 50 行）：**

```
code-runtime storage storage-json storage-domain message-feedback session-log-download
workspace session-projection-cache session-stats directory-picker plugin-inventory
api-gateway cordis-host-runner web-startup webserver web-runtime client-hmr modules
connection api-remotes client-runtime cordis-client-runner ui-theme locale ui-layout
ui-sidebar ui-settings ui-settings-general ui-settings-models ui-settings-plugin-inventory
ui-conversation ui-tool ui-cordis ui-workflow-run ui-deliverables ui-workspace
ui-input-trigger ui-commands ui-skill ui-subagent ui-jobs ui-goal ui-message-feedback
ui-model-selection ui-permission ui-agent-preset ui-settings-plugins ui-plan
ui-user-questions ui-trajectory agent-presets
```

---

## 第 2 轮 · 与 Hermes Agent 协作可行性（17:21:06 — 17:22:12）

### 2.1 用户提问

> 你扫描一下，我这个电脑里还有一个hermes agent，能和他协作吗

### 2.2 扫描结论：Hermes Agent 概况（确认在运行）

| 项目 | 状态 |
|---|---|
| 版本 | Hermes Agent **v0.20.0**，Python 3.11.15，装在 `~/.hermes/hermes-agent` |
| 运行中进程 | ① 交互会话（pts/0, PID 557）② 消息网关 `gateway run`（PID 4089）③ MCP watchdog + bocha 搜索服务 |
| 模型 | deepseek-v4-flash（与 DSH 默认同一模型）；Provider：DeepSeek + Z.AI |
| 已接平台 | 飞书（多个 DM + 群）、slack、discord、whatsapp、telegram、mattermost、matrix 配置齐全 |
| MCP | 已启用 `bocha`（网页搜索） |
| 监听端口 | 无 TCP 监听（gateway 走消息平台轮询）；后端 `serve`（JSON-RPC，默认 9119）未启动 |

### 2.3 可协作的通道（按可行度排序，原文）

**① 现在就能用 —— 通过 Shell 直接指挥 Hermes（零配置）**

DSH 有 `bash` 工具，Hermes 提供完整 CLI，双方同属 `$USER` 用户、无权限壁垒：

- `hermes chat -z "任务"` → 无头跑一个 Hermes 任务，`--resume/--continue` 延续它的会话，`--yolo` 免确认
- `hermes send -t feishu:oc_xxx "消息"` → 把消息推到 Hermes 已接的飞书等平台
- `hermes mcp list` / `hermes sessions` / `hermes status` → 只读巡检它的状态
- 共享文件系统：DSH 写 `$DSH_WORKSPACE`，Hermes 读写 `~/.hermes`，可文件交接

**② 双向工具级打通 —— 走 MCP（需要一步配置）**

- Hermes 侧现成：`hermes mcp serve` 可以把 Hermes 自己暴露成 MCP 服务器
- DSH 侧：`dsh-mcp-client` 包**已装在** profile 里，但**未接线**（web profile 插件清单没有它的行）——需在 `~/.dsh/profiles/web/cordis.patch.yml` 加一行激活后重启 web
- 反向：Hermes 也可以调 `dsh --profile headless "任务"` 把活派给 DSH

**③ 更深层编排（可逐步加）**

- DSH 起子代理 → 子代理调 Hermes；Hermes 的 cron/hooks/webhook 反过来触发 DSH
- 通过共享的 `~/.hermes/kanban.db` 看板/任务队列互相交接任务（Hermes 自带 kanban 子系统）——**这条后来成为正式管道（kanban watcher）**

### 2.4 诚实提醒（原文）

> 当前会话里我没有挂载 MCP 工具（`dsh-mcp-client` 未激活），所以「通道 ②」需要用户点头改 profile 配置并重启 web 界面才生效；「通道 ①」是现成的。

---

## 第 3 轮 · 协作方案 ① 的可观测性（17:27:21 — 17:27:46）

### 3.1 用户提问

> 我想先问你几个问题，在我选择方案1的时候你对hermes发送消息之后我能在terminal看见你发的消息并且看见hermes正在执行吗

### 3.2 结论（原文整理）

**默认情况：用户在自己的 OS 终端看不到，但能在 Web GUI 里看到**

- DSH 的 `bash` 工具是**输出捕获型**：每次调 Hermes 都是独立新进程，stdout 收回到工具结果，不会自动打到用户终端；启动 dsh web 的终端输出也被重定向到 `/tmp/dsh-web.log`
- 但 **Web GUI（127.0.0.1:3080）里能全程看到**：
  - 发的消息：对话里能看到执行的每条 bash 命令原文（如 `hermes chat -z "..."`）
  - Hermes 正在执行：以后台任务方式跑（`run_in_background`）时，Hermes 输出**实时流式**显示在 GUI 的 **Jobs 面板**
  - 结果：跑完 DSH 还会总结 Hermes 的回复

**若坚持要在终端看，两条现成途径：**

1. `tail -f ~/.hermes/logs/agent.log` —— 任何一次 `hermes chat` 的执行过程（思考、工具调用、回复）实时落进这里；gateway 处理平台消息看 `~/.hermes/logs/gateway.log`；或 `hermes logs -f agent`
2. 把任务输出 `tee` 到文件，终端 `tail -f` 跟着看

**一个关键澄清：**

- 用户机器上 PID 557 的 pts/0 终端是 Hermes 的**交互会话**；DSH 发起的 `hermes chat -z` 是**独立新进程**，其执行不会出现在那个交互终端里，只会进 `agent.log` 和 DSH 的工具输出
- `hermes send` 是即发即走的推送，没有「执行过程」可看，只有成功/失败

> 最省事的观察方式：DSH 以后台任务跑 Hermes → 用户在 GUI Jobs 面板实时看 → 跑完总结。

---

## 附注

- 会话存档解压脚本：`scripts/decompress_session.py`（按帧边界解析 magic 0xFD2FB528，逐帧独立解压后拼接）
- 轮次提取脚本：`scripts/extract_turns.py`（按行区间提取 JSONL 并规范化）
- 本会话第 1 轮回答正是后续 DSH↔Hermes 协作管道（kanban watcher 插件、/dsh-send 技能）诞生的起点，落地方案见仓库根 README 与 INSTALL-安装指南.md。
