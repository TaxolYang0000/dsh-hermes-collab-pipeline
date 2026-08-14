# Changelog

All notable changes to the DSH ↔ Hermes collaboration pipeline.

## [Unreleased / Next]
- 计划中：npm publish dsh-kanban-watcher；Hermes Agent issue（external_event_steer）。

---

## v0.2.0 — 2026-08-14 · M6 会话继承（Session Inheritance）

### 新内容（New）
- **watcher 会话继承**（dsh-kanban-watcher v0.2.0）：
  - 任务正文携带 `[会话继承:<关键词>]` 或 `[会话继承:<session-id>]` 时，
    watcher 会在同工作区内匹配历史会话并**续接上下文**（不再是每次新对话）。
  - 三种执行模式（S1 spike 实测支撑）：
    - `live-reuse`：命中仍在运行的会话 → 直接复用（方案 A）
    - `resume`：命中已结束的冷会话 → `agents.resume` 恢复事件流后续接
    - `create`：未命中 → 回退新建会话（原有行为不变）
  - 结果回写带审计字段：`继承会话: <sessionId>`
  - 规模护栏：resume 前估算 token，超 50 万告警提示新建会话
  - 会话级 guard：同一会话被第二个任务命中时跳过继承，防双开
  - cwd 特判：resume 会话沿用原 cwd（header 不可变），与 `--workspace` 冲突只记日志
- **/dsh-send 技能 v1.3.0**（Hermes 侧）：
  - 新增 `--resume <关键词>` 选项：下发任务时写入 `[会话继承:<关键词>]`
  - 用法示例：`/dsh-send --resume 继续讨论X 再分析一下`

### 变更（Changed）
- watcher 源码 337 → 588 行（parseInherit / matchSession / driveAgent / resumeOrReuse /
  estimateResumeTokens / 会话级 guard）
- 单元测试 46 用例 + 集成测试 10 用例，全部通过（0 失败）

### 修复（Fixed）
- 上一版"每次下发都是新对话"：现在可继承历史会话上下文

### 验证（Verified）
- 实测：第一轮建上下文 → 第二轮 `[会话继承:会话继承测试]` 命中同一会话，
  agent 明确复述上一轮内容（"记得创建了 inherit-test-round1.txt，内容 round1-deepseek-v4-flash"），
  结果带继承会话 id 审计字段。

---

## v0.1.0 — 2026-08-14 · Initial Release

### 新内容（New）
- **dsh-kanban-watcher 插件 v0.1.0**：监听 Hermes kanban board `dsh`，
  把 ready 任务交给 DSH Agent 在 Web GUI 会话执行，回写看板 + done 文件
  - 事件驱动唤醒（trigger 文件 + fs.watch + 30s 兜底轮询）
  - 原子认领防重复执行、串行执行、崩溃恢复（singleton lock + reclaim）
  - 模型翻译（modelMap）、输出白名单、hermes-trusted 权限预设
- **external_event_steer**（Hermes cli.py + config_defaults.py patch）：
  - CLI 会话空闲时监听 `~/.dsh/kanban-done/`，新 done 文件注入【外部通知】到当前会话
  - done 文件视为不可信输入（只读 id/title/result、截断、剥控制字符、从不执行）
  - 配置开关 `features.external_event_steer`（默认关）
- **/dsh-send 技能 v1.2.x**：Hermes 侧下发任务（模型/工作区/幂等键/技能传递）
- **install.sh**：一键自动安装（幂等、agent 可用：`--yes` 全自动、`--dry-run` 预演）
- **文档**：双语 README、INSTALL 指南、NOTICE（借鉴合规）、能力盘点与可行性

### 说明
- 全部代码由 DeepSeek AI 生成，未经人工审查（详见 README AI-GENERATED CODE NOTICE）。
- MIT License（Copyright © 2026 TaxolYang0000）。
