# 安装指南（面向新人 · 从零复现）

> **English version: [INSTALL.md](INSTALL.md)**

> 目标：让一个**全新环境**（没装过 DSH/Hermes 协作管道）的人，按本文档能完整复现。
> 前提：一台 Linux/WSL 机器，能访问 GitHub，有 Node.js 18+ 和 Python 3.10+。

## 第 0 步：一键脚本（推荐，替代第 3~7 步的手动操作）

如果你只想快速装好，仓库根目录的 `install.sh` 会自动化第 2~7 步：

```bash
./install.sh --dry-run    # 先预演，看它要做什么
./install.sh --yes        # 全自动安装（幂等，可重跑；AI Agent 也用它）
```

脚本自动：初始化 kanban board → 安装插件 → 挂载 cordis.patch.yml → 应用 Hermes patch →
开启配置 → 部署技能 → 生成 systemd 服务模板 → 验证。
前置条件不满足时退出码 2 并提示怎么补。

> 注意：一键脚本不替代第 1~2 步（装 Agent、clone 仓库），也不替代第一次 `dsh web`
> 初始化 profile。以下手动步骤供参考/排查用。

## 第 1 步：安装两个 Agent（如果还没有）

```bash
# Hermes Agent（官方安装脚本）
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

# DSH / DeepSeek Harness（npm 全局）
npm install -g @deepseek-ai/dsh

# 确认
hermes --version
dsh --version
```

> 注意：DSH 的 TUI 已被官方移除，当前只有 Web UI（`dsh web`）和 headless 模式。

## 第 2 步：clone 主仓库

```bash
git clone --recurse-submodules https://github.com/TaxolYang0000/dsh-hermes-collab-pipeline.git
cd dsh-hermes-collab-pipeline
```

## 第 3 步：初始化 Hermes kanban 看板

```bash
# 创建 board dsh（只做一次；重复执行会报已存在，忽略即可）
hermes kanban boards create dsh
# 验证
hermes kanban boards          # 应看到 dsh
```

## 第 4 步：DSH 侧——安装 watcher 插件

```bash
# 3.1 初始化 DSH web profile（首次启动会自动创建 ~/.dsh/profiles/web）
dsh web --port 3080 &         # 启动后 Ctrl+C 停掉，或留着跑
# 或者用 headless 初始化：
dsh --profile web init

# 3.2 在 web profile 里加插件依赖
cd ~/.dsh/profiles/web
pnpm add file:<你的clone路径>/dsh-side/plugins/dsh-kanban-watcher
# 预期输出 dsh: warning: dsh-kanban-watcher declares no dsh.bundle —— 属预期

# 3.3 挂载插件行（编辑 ~/.dsh/profiles/web/cordis.patch.yml，追加）
cat >> ~/.dsh/profiles/web/cordis.patch.yml << 'EOF'
- insert:
    - id: kanban-watcher
      name: 'dsh-kanban-watcher'
      config:
        board: 'dsh'
        assignee: 'dsh'
        triggerDir: '~/.dsh/kanban-trigger'
        pollIntervalMs: 30000
        allowedOutputDirs:
          - '<你的DSH工作区>'
        modelMap:
          'deepseek-v4-flash': { provider: 'deepseek-official', model: 'deepseek-v4-flash' }
          '__fallback__':      { provider: 'deepseek-official', model: 'deepseek-v4-flash' }
EOF

# 3.4 重启 dsh web 使插件生效
pkill -f "dsh web --port 3080" || true
nohup dsh web --port 3080 > /tmp/dsh-web.log 2>&1 &
# 验证：tail -f /tmp/dsh-web.log 出现 kanban-watcher started
```

> ⚠️ 重要：`triggerDir`、`allowedOutputDirs` 里的路径**必须按你的机器改**。
> 插件配置的 `hermesBin` 默认是 `~/.local/bin/hermes`，如果你的 hermes 在别处也要改。

## 第 5 步：Hermes 侧——应用补丁（可选）+ 部署技能

> 补丁是**可选的**。不打补丁，管道 100% 工作（下发 → 执行 → 看板回写），只是少了 CLI 自动弹出【外部通知】。如果 `git apply` 失败（Hermes 版本差异），跳过本步即可——只有确实想要自动弹出时才看「patch 冲突处理」。

```bash
# 4.1 应用外部事件注入 patch（改 Hermes 源码）
cd ~/.hermes/hermes-agent
git apply <你的clone路径>/hermes-side/hermes-external-event-steer.patch
# 若失败（版本差异），手动改：见「patch 冲突处理」节

# 4.2 开启配置开关
hermes config set features.external_event_steer true

# 4.3 部署 /dsh-send 技能（放到 Hermes 技能目录）
mkdir -p ~/.hermes/skills/devops
cp -r <你的clone路径>/hermes-side/dsh-send-skill ~/.hermes/skills/devops/dsh-send

# 4.4 部署 /inbox 快命令（可选，配置进 config.yaml 的 quick_commands 段）
# 参考 hermes-side/quick_commands.yml

# 4.5 重启 Hermes CLI 会话（新代码 + 新技能生效）
```

## 第 6 步：systemd 服务（可选但推荐）

```bash
# 编辑模板（替换 <DSH_BIN> 和 <NPM_PREFIX>）
cp hermes-side/dsh-web.service ~/.config/systemd/user/dsh-web.service
# 编辑 ~/.config/systemd/user/dsh-web.service 里的占位符
systemctl --user daemon-reload
systemctl --user enable --now dsh-web.service
systemctl --user status dsh-web.service   # 应 active
```

## 第 7 步：验证

```bash
# 在 Hermes 会话里：
/dsh-send 测试一下，写一句话到 DSH 工作区

# 预期：
# 1. 看板出现任务（hermes kanban --board dsh list）
# 2. DSH Web GUI (127.0.0.1:3080) 自动开会话执行
# 3. 完成时 Hermes 会话自动弹出【外部通知】任务 xxx 已完成
```

## patch 冲突处理（版本差异时）

如果 `git apply` 失败，说明你的 Hermes 版本与 patch 基线不同。两种处理：

```bash
# 方法 A：用 git apply 3-way（自动合并）
git apply -3 hermes-external-event-steer.patch

# 方法 B：手动改（patch 只有 104 行，改动点清晰）
#   cli.py：新增 _drain_done_notifications() 方法 + 空闲循环调用（2 处）
#   config_defaults.py：features 配置段（1 处）
# 详见 hermes-side/PR-提交说明.md 的「改动文件」节
```

## 常见问题（已知坑）

1. **插件更新必须重启 dsh web**：node 不热重载，改插件代码后必须 `pkill -f "dsh web"` + 重启
2. **seen baseline 时序**：done 目录首次出现时已有的文件会被跳过（不会重放）。验证通知链路时，
   先确保目录已存在并初始化，再写入新的 done 文件
3. **SQLite 锁**：Hermes 和 watcher 同时写 kanban.db 可能 busy，watcher 已内置重试（3 次）
4. **串行执行**：同一时刻只跑一个任务，后续排队
5. **权限预设**：watcher 会话用 danger-full-access（hermes-trusted），安全边界靠 Hermes 侧白名单，
   不要给不可信任务源开放
6. **版本绑定**：插件依赖 `@deepseek-ai/dsh-*@0.1.0-rc.6`，与你安装的 DSH 版本一致。
   npm `latest` dist-tag 可能指向旧版（0.0.1-rc.1），但 profile 内实际安装的是 0.1.0-rc.6——
   装插件时以 profile 内的版本为准，`pnpm add file:` 会复用 profile 已有依赖
