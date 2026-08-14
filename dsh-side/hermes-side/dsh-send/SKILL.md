---
name: dsh-send
description: "把任务下发给 DSH（DeepSeek Harness Web 端），可带模型/设置选项。用法：/dsh-send [--model M] [--provider P] [--resume <关键词>] 任务内容。DSH 会在 Web GUI 自动执行并在看板回写结果。"
version: 1.3.0
---

# 向 DSH 下发任务

## 触发
用户输入 `/dsh-send <选项> <任务内容>`，或明确说「交给 DSH / 发给 Web 端」。

## 流程
1. 解析用户指令里的选项（`--model`、`--provider`、`--priority`、`--max-runtime`、`--workspace dir:<path>`、`--idempotency-key <key>`、`--skill <name>`、`--resume <关键词>`），未指定则用 Hermes 当前默认模型。
2. **落点分配与白名单校验（v1.3.4 必做）**：默认落点 = **在 DSH 工作区（$DSH_WORKSPACE）内新建一个合适命名的文件夹存放输出，输出路径写在结果里**（命名由 DSH agent 按任务内容自定）；如需特定路径（如桌面 $DESKTOP）可显式说明。所有落点必须 ∈ Hermes 侧白名单（`$DSH_WORKSPACE`、`$DESKTOP/` 及后续扩展），**不在白名单则拒绝下发**并说明原因。
3. **技能传递（v1.3.6 方案 C，--skill <name> 可选）**：若用户指定 `--skill <name>`（如 `--skill two-step-t1-dip-buy-strategy`），把该 skill 复制到共享区 `$DSH_WORKSPACE/skills-shared/<name>/`（含 SKILL.md 及 references/ 等全部文件），并在任务正文写入 `【参考技能】<共享区路径>`。DSH agent 从共享区（自己领地）读 skill 内容，不跨域读 ~/.hermes。复制用 `cp -r ~/.hermes/skills/<category>/<name> $DSH_WORKSPACE/skills-shared/`（先按名搜 skills_list 定位 category）。找不到 skill 则报错并终止下发。
4. **会话继承（v1.3.0 方案 A，--resume <关键词> 可选）**：若用户指定 `--resume <关键词>`（或显式 `<session-id>`），在任务正文写入 `[会话继承:<关键词>]`。watcher 会用关键词模糊匹配同工作区历史会话标题：命中 live 会话 → 直接复用续接；冷会话 → resume 恢复上下文；未命中 → 回退新建会话。不指定则不继承（每次新对话）。
5. 用 `hermes kanban create` 创建任务（看板 `dsh`，assignee `dsh`，模型/设置原样传入）：
   ```bash
   hermes kanban --board dsh create "<任务内容>（输出要求：在 DSH 工作区内新建合适命名文件夹存放，路径写进结果）[会话继承:<关键词>]【参考技能】$DSH_WORKSPACE/skills-shared/<name>/" \
     --assignee dsh --created-by hermes --json \
     [--model <M>] [--provider <P>] [--priority <N>] \
     [--max-runtime <dur>] [--workspace dir:<path>] \
     [--idempotency-key <key>] [--initial-status ready]
   ```
   > ⚠️ 实测（2026-08-14）：`--model/--provider` 存为 `model_override/provider_override` 字段；create 后任务初始状态为 `ready`（非 todo）。**`create` 无 `--output-dir` 参数**——落点必须并入任务正文，不能作为 CLI flag 传。
   > ⚠️ 会话继承（v1.3.0 已实现）：`--resume <关键词>` 让 DSH 继承历史会话上下文（live 复用 or 冷 resume）。未命中关键词时回退新建会话，不影响正常下发。规模护栏：超长会话（>50 万 token 预估）会告警提示新建。
6. **写触发文件**（事件驱动唤醒 watcher）：`echo <task_id> > ~/.dsh/kanban-trigger/<task_id>.trigger`（目录不存在则 `mkdir -p`）。
7. 把返回的任务 id 告诉用户：任务已投递，DSH 的 Web GUI 会自动开始执行；查看结果用 `hermes kanban --board dsh show <id>` 或 `/inbox`。

## 注意
- 任务内容要自包含（DSH 没有你的会话上下文）：给出明确目标、涉及路径、期望产出（落点）。
- 不要改看板状态（认领/完成由 DSH 侧负责）。
- 白名单是 Hermes 侧唯一事实源；DSH watcher 的权限预设镜像同一白名单。
- `--workspace` 只接受 `scratch | worktree | worktree:<path> | dir:<path>` 四种取值（实测），`dir:` 前缀用于指定工作目录。
- `--idempotency-key` 用于幂等去重：重复 create 返回同一任务 id，不重复执行。
- `--initial-status` 可选：`blocked` 或 `running`（默认 `ready`，实测 VALID_STATUSES 九态），通常不需要显式传。`create` 支持的全部合法参数以 `hermes kanban create --help` 为准。
- `--skill <name>`（v1.3.6 方案 C）：技能复制到 $DSH_WORKSPACE/skills-shared/ 共享区（DSH 领地），任务正文只写路径；skill 更新后需重新复制。不跨域读 ~/.hermes。
- `--resume <关键词>`（v1.3.0 会话继承）：用于延续之前对话的上下文（如"继续讨论X"）。关键词匹配历史会话标题；显式 session-id 更精确。继承的会话 cwd 沿用原值（resume 会话工作目录不可变）。
