# PR / Issue 提交说明：external_event_steer

> 用途：提交给 Hermes Agent 官方仓库（NousResearch/hermes-agent）时的配套说明
> ⚠️ 本功能代码由 DeepSeek 模型生成，未经人工审查

## Issue 标题（建议）

`feat(cli): external event steering — inject external agent task-completion notifications into CLI session`

## Issue 正文

### 动机

在与外部 AI agent（如 DSH / DeepSeek Harness）协作的场景中，Hermes 下发任务后
需要感知外部 agent 的完成状态。当前没有机制：CLI 会话只能被动等用户输入或主动轮询。

本功能让 Hermes CLI 会话能感知外部系统的完成通知：外部 agent 完成任务后写一个
JSON done 文件到固定目录，Hermes 空闲循环检测到新文件后注入一条【外部通知】
消息到当前会话。

### 设计

- **done 文件格式**：`<id>.done` JSON，字段 `{id, title, result, ts, status}`
- **监听目录**：默认 `~/.dsh/kanban-done/`，可用环境变量 `HERMES_DONE_WATCH_DIR` 覆盖
- **注入时机**：CLI process_loop 空闲分支（`_agent_running` 为 false 时），每 0.1s 轮询
- **seen baseline**：启动时记录目录已有文件，只处理新事件，不重放旧事件
- **配置开关**：`features.external_event_steer`（默认 false，显式开启才生效）

### 安全边界

- done 文件 JSON 视为**不可信输入**：只读 `id`/`title`/`result` 三字段
- 值截断（id 40 / title 60 / result 200 字符）+ 剥除控制字符
- 文件内容**从不执行**，只是拼进一条文本消息
- 异常静默捕获，绝不让损坏文件打断主循环

### 改动文件

- `cli.py`：新增 `_drain_done_notifications()` + process_loop 空闲分支调用（+60 行）
- `hermes_cli/config_defaults.py`：新增 `features` 配置段（+12 行）

### 适用场景

- Hermes + DSH 双 Agent 协作（本仓库主场景）
- 任何「外部系统写 done 文件 → Hermes 会话感知」的场景

### 备选方案考虑

- 插件方式（不碰 cli.py）：需要访问 `_pending_input`，插件 API 暴露不足，改核心更直接
- 轮询看板：会话侧无看板上下文，done 文件是最小耦合

## PR 提交检查清单

- [ ] 与 maintainer 讨论过（issue 先开）
- [ ] 代码风格符合项目（参见 AGENTS.md Contribution Rubric）
- [ ] 测试覆盖：done 文件写入 → 注入；seen baseline 不重放；损坏文件不崩溃
- [ ] 文档：config_defaults.py 注释已写
- [ ] 未引入新依赖

## 备注

- patch 文件：`hermes-external-event-steer.patch`（104 行，git apply 可直接应用）
- 安全设计说明见仓库根 README 的「工作原理」与「安全设计」节
