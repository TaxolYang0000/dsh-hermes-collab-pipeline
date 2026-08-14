# dsh-kanban-watcher

> ⚠️ **AI 生成代码声明**：本插件代码由 DeepSeek 模型生成，未经人工审查。使用风险自负；部署前请人工审查安全关键路径（权限预设、白名单、文件写入）。

DSH ↔ Hermes 双 Agent 协作管道的**看板执行侧插件**：监听 Hermes kanban 任务队列，把任务交给 DSH Agent 在 Web GUI 会话中执行，并把结果回写看板与 done 文件。

- 运行环境：DeepSeek Harness（DSH）web profile 内的 Cordis 插件（常驻在 web host 进程里）
- 依赖方：Hermes Agent（Python）——负责下发任务、维护看板、接收完成通知
- 一句话：**Hermes 说「去做 X」→ 看板出现任务 → 本插件唤醒 DSH Agent 干活 → 结果回写看板 + 写 done 文件通知 Hermes**

## 适用场景

本插件解决的是**同一台机器上跑两套独立 Agent（DSH + Hermes）时，任务如何跨系统交接**的问题：

| 场景 | 说明 |
|---|---|
| 双 Agent 协作 | 你在 Hermes 终端下发任务（`/dsh-send`），DSH 在 Web GUI 里自动开会话执行，全程可见可回看 |
| kanban 看板任务队列 | 任务队列用 Hermes 自带 kanban（`~/.hermes/kanban.db`，board `dsh`），原生支持元数据、原子认领、状态机、评论、崩溃恢复 |
| 无人值守执行 | watcher 会话使用专用权限预设（danger-full-access + never），白名单落点免审批写入，不需要人工点批准 |
| 结果双端可见 | DSH 侧：执行会话永久留在 GUI 会话列表；Hermes 侧：看板评论里有结果摘要，done 文件触发外部事件注入到 Hermes 当前会话 |

**不适合**：单 Agent 场景（不需要看板）；需要并发执行多任务的场景（v1 为串行）；跨机器部署（默认假设 DSH 与 Hermes 同机、同用户）。

## 工作原理

```
Hermes 终端                        DSH web host                       Hermes 侧
─────────────                      ──────────────                     ─────────
/dsh-send "任务"   ──create──▶  看板(kanban.db, board=dsh)
  (skill)           ──触发文件──▶  ~/.dsh/kanban-trigger/<id>.trigger
                                    │ fs.watch 事件驱动唤醒
                                    ▼
                                  claim <id>（原子认领）
                                  show <id> --json（读元数据）
                                  agents.create（开 GUI 会话）
                                  followup(任务) → agent 执行
                                  │  withTimeout 硬超时兜底(600s)
                                  ▼
                                  comment + complete --result   ──▶ 看板回写（/inbox 可见）
                                  writeDoneFile(<id>.done)      ──▶ ~/.dsh/kanban-done/<id>.done
                                                                     → Hermes 空闲循环发现，注入当前会话
```

关键设计：

- **事件驱动唤醒**：Hermes 创建任务后写触发文件（`~/.dsh/kanban-trigger/<id>.trigger`），插件用 `fs.watch` 监听该目录，毫秒级唤醒；另有 30s 低频兜底轮询防事件丢失。
- **原子认领防重复执行**：只认领 `status === "ready"` 的任务，`claim` 由 kanban 保证单次；`running` 集合防同 tick 内重复。
- **串行执行**：同一时刻只执行一个任务，后续排队（v1 设计）。
- **崩溃恢复**：watcher 启动时扫描 `running` 状态任务，`reclaim` 退回 `ready`（上次执行中断）；自身带 singleton lock（PID + 存活检查）防双开。
- **模型翻译**：Hermes 的模型规格（`model_override`/`provider_override`）经 `modelMap` 映射为 DSH 的 provider/model，翻译不到走 `__fallback__`，实际使用模型回写进结果。
- **会话可见**：每个任务独立 `session-hermes-<id>-<uuid>` 会话并 attach 到工作区，GUI 侧边栏实时出现、可点开、刷新仍在。

## 安装

本插件不是 `dsh.bundle` 补丁层，而是一个 **Cordis 插件包**：装入 web profile 依赖后由 loader 直接 import。

### 1. 加依赖（在 web profile 目录下）

```bash
cd ~/.dsh/profiles/web
pnpm add file:<你的clone路径>/dsh-side/plugins/dsh-kanban-watcher
```

> 预期输出 `dsh: warning: dsh-kanban-watcher declares no dsh.bundle` —— **属预期**，插件只需被 loader import，不需要成为补丁层。

### 2. 挂载插件行（`~/.dsh/profiles/web/cordis.patch.yml`）

```yaml
- insert:
    - id: kanban-watcher
      name: 'dsh-kanban-watcher'
      config:
        board: 'dsh'
        assignee: 'dsh'
        triggerDir: '$DSH_TRIGGER_DIR'
        pollIntervalMs: 30000
        allowedOutputDirs:
          - '$DSH_WORKSPACE'
          - '$DESKTOP'
        modelMap:
          'deepseek-v4-flash': { provider: 'deepseek-official', model: 'deepseek-v4-flash' }
          '__fallback__':      { provider: 'deepseek-official', model: 'deepseek-v4-flash' }
```

### 3. 重启 web

```bash
pkill -f "dsh web --port 3080"   # 先杀干净（铁律），再启动
nohup $DSH_BIN web --port 3080 > /tmp/dsh-web.log 2>&1 &
```

验证：`tail -f /tmp/dsh-web.log` 出现 `kanban-watcher started`。

## 配置项

全部配置走 `cordis.patch.yml` 里插件行的 `config`，均有默认值：

| 键 | 默认值 | 说明 |
|---|---|---|
| `hermesBin` | `$HERMES_BIN` | `hermes` CLI 可执行文件路径（kanban 子命令入口） |
| `board` | `dsh` | 看板名；与 Hermes 侧 `/dsh-send` 创建任务用的 board 一致 |
| `assignee` | `dsh` | 认领归属人；只处理 assignee 为 `dsh` 的任务 |
| `triggerDir` | `$DSH_TRIGGER_DIR` | **触发文件目录**：Hermes 下发任务后写 `<id>.trigger` 到此，`fs.watch` 监听事件驱动唤醒 |
| `doneDir` | `$DSH_DONE_DIR` | **done 文件目录**：任务完成后写 `<id>.done` 到此；Hermes 外部事件注入（`external_event_steer`）默认监听这里，可用 `HERMES_DONE_WATCH_DIR` 覆盖 |
| `pollIntervalMs` | `30000` | 兜底轮询间隔（fs.watch 事件可能合并/丢失） |
| `taskTimeoutMs` | `600000` | 单任务硬超时（10 分钟）；超时释放 agent 会话并走错误上报，防审批挂起拖死管道 |
| `permissionPreset` | `hermes-trusted` | watcher 会话专用权限预设（danger-full-access + never）：白名单落点免审批写、升级请求快速失败 |
| `cwd` | `$DSH_WORKSPACE` | 任务未指定工作区时的默认工作目录 |
| `allowedOutputDirs` | `["$DSH_WORKSPACE", "$DESKTOP"]` | 输出落点白名单（镜像 Hermes 下发侧白名单；拦截仍在 Hermes 侧） |
| `modelMap` | flash→flash / `__fallback__` | Hermes 模型规格 → DSH provider/model 翻译表；`__fallback__` 为兜底 |

> ⚠️ 安全权衡（必读）：`hermes-trusted` = danger-full-access + never，watcher 会话拥有全盘写权限。**安全边界依赖 Hermes 下发侧白名单（任务源头过滤）**，不是沙箱。对不可信任务源需要另行防护。

## 使用

### 从 Hermes 侧下发任务（上游）

Hermes 侧用技能 `/dsh-send`（见 `hermes-side/dsh-send-skill/SKILL.md`）：

```text
/dsh-send --model deepseek-v4-flash 写一份本周进展周报
```

`/dsh-send` 会：创建 kanban 任务（`hermes kanban --board dsh create ... --assignee dsh --created-by hermes --json`）→ 写触发文件 `~/.dsh/kanban-trigger/<id>.trigger` → 返回任务 id。

### watcher 认领执行（本插件）

1. `fs.watch` 收到触发文件事件（或 30s 兜底轮询），`drainOnce` 启动；
2. `list --json --assignee dsh` 找 `ready` 任务 → `claim <id>`（原子认领）→ `show <id> --json` 读元数据；
3. 按 `model_override`/`provider_override` 走 `modelMap` 翻译，`agents.create` 开 GUI 会话（挂 standard preset + hermes-trusted 权限预设），`followup` 注入任务，`withTimeout` 兜底；
4. 执行完成后 `comment` + `complete --result` 回写看板，再 `writeDoneFile` 写 `<id>.done`。

### 查看结果（Hermes 侧）

```bash
hermes kanban --board dsh show <id>     # 看板详情 + 评论
/inbox                                  # 任务队列（只读查看）
```

DSH 侧：Web GUI 会话列表出现「📥 来自 Hermes：...」会话，点开可回看完整执行过程；done 文件会让 Hermes 当前会话自动收到【外部通知】。

## 目录结构

```
dsh-kanban-watcher/
├── lib/
│   └── index.js        # 插件主体（单文件，~340 行）
├── package.json        # 包声明（Cordis 插件，非 bundle 补丁）
└── README.md
```

## 开发者说明

- 源码唯一事实源 = 仓库；部署经 `pnpm add file:` 链接到 `~/.dsh/profiles/web/node_modules/`，改源码后**必须重启 dsh web 才生效**（运行中的 node 进程不热重载插件代码）。
- 对 Hermes kanban CLI 的字段事实（`list --json` 纯数组、`show` 取 `.task`、`claim` 无 `--assignee`、`comment` 位置参数、终态 `done` 等）已实测确认，见 `lib/index.js` 头部注释。

## License

MIT
