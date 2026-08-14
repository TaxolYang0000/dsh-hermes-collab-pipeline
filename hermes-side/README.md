# Hermes 侧组件：外部事件注入（external_event_steer）

> ⚠️ **AI 生成代码声明**：本组件代码由 DeepSeek 模型生成，未经人工审查。使用风险自负；应用 patch 前请人工审查（涉及 Hermes 源码 cli.py 改动）。

这是 DSH↔Hermes 双 Agent 协作管道中 **Hermes 侧**的改动。
它让 Hermes CLI 会话能感知外部 agent（如 DSH watcher）完成的任务，
无需轮询看板、无需手动输入——任务完成时自动在会话里弹出【外部通知】。

## 适合什么情况

你在运行 **Hermes Agent**（CLI 或交互会话），并且：

- 有一个**外部执行器**（比如 DSH/DeepSeek Harness 的 watcher 插件）
- 它在完成任务后能写一个 JSON 文件到固定目录（默认 `~/.dsh/kanban-done/`）
- 你希望 Hermes 会话**主动感知**任务完成，而不是等你自己去查

典型场景：Hermes 下发任务 → DSH 执行 → 写 done 文件 → Hermes 会话自动弹出
「任务 xxx 已完成。结果摘要：...」。

## 包含内容

| 文件 | 说明 |
|------|------|
| `hermes-external-event-steer.patch` | 对 Hermes 源码的 diff（cli.py + hermes_cli/config_defaults.py），104 行 |
| `dsh-send-skill/` | Hermes 侧 `/dsh-send` 技能（SKILL.md），用于向 DSH 下发任务 |
| `quick_commands.yml` | `/inbox` 快命令配置（查看看板队列） |
| `dsh-web.service` | DSH Web UI 的 systemd 用户服务文件（常驻启动） |

## 怎么安装

```bash
# 1. 进入 Hermes 源码目录
cd ~/.hermes/hermes-agent

# 2. 应用 patch（升级 Hermes 后重新应用，先 git status 确认无冲突）
git apply hermes-external-event-steer.patch

# 3. 开启配置开关（config.yaml 的 features 段）
hermes config set features.external_event_steer true

# 4. 重启 Hermes CLI 会话（新代码生效）
```

## 工作原理

```
DSH watcher 完成任务
      │  writeDoneFile() → 写 ~/.dsh/kanban-done/<id>.done
      ▼
JSON 文件（{id, title, result, ts, status}）
      │  Hermes CLI 空闲循环每 0.1s 轮询 _drain_done_notifications()
      ▼
检测到新 .done 文件（不在 seen baseline 中）
      │  提取 id/title/result，截断 + 剥控制字符
      ▼
注入 _pending_input → 会话自动弹出【外部通知】消息
```

## 安全设计

- done 文件 JSON 视为**不可信输入**：只读 `id`/`title`/`result` 三个字段
- 所有值截断（id 40 字符 / title 60 / result 200）并剥除控制字符
- 文件内容**从不执行**——只是拼进一条文本消息
- 启动时建立 seen baseline：已有文件不重放，只处理新事件
- 功能默认**关闭**（`features.external_event_steer: false`），显式开启才生效

## 配置项

| 配置 | 默认值 | 说明 |
|------|--------|------|
| `features.external_event_steer` | `false` | 总开关 |
| 环境变量 `HERMES_DONE_WATCH_DIR` | `~/.dsh/kanban-done` | done 文件监听目录 |

## 已知限制

- 只作用于 **CLI 会话**（cli.py 主循环空闲分支）；gateway/飞书等平台不走这条注入
- seen baseline 时序陷阱：若 done 目录首次出现时已存在文件，会被当作基线跳过
  （验证链路时：先确保目录已存在并初始化，再写入新文件）
