# 借鉴来源与 License 合规声明（NOTICE）

> 更新日期：2026-08-14
> 本仓库所有代码由 DeepSeek 模型生成（未经人工审查），但开发过程中参考了以下
> GitHub 开源项目的思路与少量代码。根据各项目 License 要求，特此声明并保留版权。

## 一、借鉴来源清单

| 项目 | 仓库 | License | 借鉴内容 | 借鉴程度 |
|------|------|---------|---------|---------|
| DeepSeek Harness (DSH) | deepseek-ai/deepseek-harness | MIT | 插件机制（Cordis bundle）、agents.create/sessions/workspaceRegistry API 用法、会话存档格式（zstd 拼接帧） | API 使用 + 思路借鉴 |
| Hermes Agent | NousResearch/hermes-agent | MIT | kanban CLI 用法、kanban_watchers.py 的 singleton lock 设计思路、CLI 空闲循环结构 | 思路借鉴（无代码复制） |
| dsh-harness-mcp-server | chushixixin/dsh-harness-mcp-server（本地审查副本在 review/） | MIT | 权限预设挂载方式（agentPresets.mount）、会话 attach 工作区 | 思路借鉴（无代码复制） |
| DSH headless summarize | @deepseek-ai/dsh 内置 | MIT | `summarize()` 函数（汇总最后 assistant 文本与结束原因） | **实质性代码参考**（lib/index.js 中标注「照抄 headless.summarize」） |
| dsh-kanban | Ericwong5021/dsh-kanban | MIT | 无（React Web UI 看板，与我们的后台执行插件完全不同类型，仅命名相似） | 无借鉴，仅生态关联提及 |

## 二、各 License 的合规义务

所有借鉴来源均为 **MIT License**。MIT 的核心义务：

1. **保留版权声明**：在复制或实质性修改的代码中，必须保留原始版权声明和许可声明
2. **附带许可文本**：分发时须包含 MIT License 全文

## 三、我们的处理方式

### 3.1 实质性借鉴的部分（需保留版权声明）

**`summarize()` 函数**（dsh-side/plugins/dsh-kanban-watcher/lib/index.js）：
- 来源：DeepSeek Harness headless 模式的 summarize 逻辑（MIT）
- 处理：函数头部已标注来源；本 NOTICE 声明保留 DeepSeek 版权

### 3.2 思路借鉴的部分（无代码复制，注明来源即可）

- DSH 插件机制 / API 用法：使用官方公开 API，属正常使用
- Hermes kanban CLI：通过 CLI 交互（非代码复制）
- singleton lock 设计思路：借鉴思想，独立实现（PID + kill(pid,0) 存活检查）
- 权限预设挂载：使用 DSH 公开 API（agentPresets.mount），非复制

### 3.3 建议的最终合规动作（上传 GitHub 前）

1. **LICENSE 文件**：仓库根目录放 MIT License，版权人 TaxolYang0000（GitHub 昵称）
2. **NOTICE 文件**：本文件（已备好），随仓库一起上传
3. **代码内标注**：summarize() 函数头部标注「Adapted from DeepSeek Harness (MIT)」
4. **dsh-kanban 生态提及**：README 的 Related/生态节提及 Ericwong5021/dsh-kanban（同领域项目）

## 四、不需要担心的情况

- ❌ 没有复制 GPL/Apache 等有 copyleft 或附加条款的代码（全部来源是 MIT）
- ❌ 没有使用任何闭源代码
- ❌ 没有复制 Ericwong5021/dsh-kanban 的代码（类型不同，无重叠）
- ❌ 没有引入 API key、凭据等敏感信息（已脱敏）

## 五、各来源版权声明原文（MIT 要求保留）

```
DeepSeek Harness (DSH)
MIT License
Copyright (c) 2026 DeepSeek

Hermes Agent
MIT License
Copyright (c) 2025 Nous Research

dsh-harness-mcp-server
MIT License
Copyright (c) 2026 Chusxxin

dsh-kanban
MIT License
Copyright (c) 2026 Ericwong5021
```
