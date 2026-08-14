# Installation Guide (from scratch)

> Goal: let someone on a **fresh machine** (never installed the DSH↔Hermes pipeline)
> reproduce the full setup by following this doc.
> Prerequisites: a Linux/WSL machine with GitHub access, Node.js 18+ and Python 3.10+.
> 中文版见 [INSTALL-安装指南.md](INSTALL-安装指南.md)

## Step 0: One-command installer (recommended, replaces manual Steps 3–7)

```bash
./install.sh --dry-run    # preview what it will do
./install.sh --yes        # fully automatic (idempotent, re-runnable; AI agents use this too)
```

The script auto: initializes the kanban board → installs the plugin → mounts
`cordis.patch.yml` → applies the Hermes patch → enables the feature → deploys the
skill → generates a systemd service template → verifies. It exits with code 2 and
fix hints when prerequisites are missing.

> Note: the one-command script does NOT replace Steps 1–2 (installing the agents,
> cloning the repo), nor the first `dsh web` profile initialization. The manual
> steps below are for reference / troubleshooting.

## Step 1: Install the two agents (if you don't have them)

```bash
# Hermes Agent (official install script)
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

# DSH / DeepSeek Harness (npm global)
npm install -g @deepseek-ai/dsh

# Verify
hermes --version
dsh --version
```

> Note: DSH's TUI was removed by the official team; only the Web UI (`dsh web`)
> and headless mode remain.

## Step 2: Clone the main repository

```bash
git clone --recurse-submodules https://github.com/TaxolYang0000/dsh-hermes-collab-pipeline.git
cd dsh-hermes-collab-pipeline
```

## Step 3: Initialize the Hermes kanban board

```bash
# Create board "dsh" (once; re-running reports "already exists", ignore it)
hermes kanban boards create dsh
# Verify
hermes kanban boards          # you should see "dsh"
```

## Step 4: DSH side — install the watcher plugin

```bash
# 4.1 Initialize the DSH web profile (first start auto-creates ~/.dsh/profiles/web)
dsh web --port 3080 &         # Ctrl+C to stop after init, or leave it running
# Or initialize headlessly:
dsh --profile web init

# 4.2 Add the plugin as a dependency in the web profile
cd ~/.dsh/profiles/web
pnpm add file:<your-clone-path>/dsh-side/plugins/dsh-kanban-watcher
# Expected output: dsh: warning: dsh-kanban-watcher declares no dsh.bundle — this is NORMAL

# 4.3 Mount the plugin line (append to ~/.dsh/profiles/web/cordis.patch.yml)
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
          - '<your-DSH-workspace>'
        modelMap:
          'deepseek-v4-flash': { provider: 'deepseek-official', model: 'deepseek-v4-flash' }
          '__fallback__':      { provider: 'deepseek-official', model: 'deepseek-v4-flash' }
EOF

# 4.4 Restart dsh web so the plugin loads
pkill -f "dsh web --port 3080" || true
nohup dsh web --port 3080 > /tmp/dsh-web.log 2>&1 &
# Verify: tail -f /tmp/dsh-web.log shows "kanban-watcher started"
```

> ⚠️ Important: `triggerDir`, `allowedOutputDirs` MUST be changed to match your
> machine. The plugin's default `hermesBin` is `~/.local/bin/hermes` — change it
> if your hermes lives elsewhere.

## Step 5: Hermes side — apply the patch + deploy the skill

```bash
# 5.1 Apply the external-event-injection patch (modifies Hermes source)
cd ~/.hermes/hermes-agent
git apply <your-clone-path>/hermes-side/hermes-external-event-steer.patch
# If it fails (version drift): see the "patch conflict handling" section below

# 5.2 Enable the feature flag
hermes config set features.external_event_steer true

# 5.3 Deploy the /dsh-send skill (into Hermes' skills dir)
mkdir -p ~/.hermes/skills/devops
cp -r <your-clone-path>/hermes-side/dsh-send-skill ~/.hermes/skills/devops/dsh-send

# 5.4 Deploy the /inbox quick command (optional; merge into config.yaml's quick_commands section)
# See hermes-side/quick_commands.yml

# 5.5 Restart the Hermes CLI session (new code + new skill take effect)
```

## Step 6: systemd service (optional but recommended)

```bash
# Edit the template (replace <DSH_BIN> and <NPM_PREFIX>)
cp hermes-side/dsh-web.service ~/.config/systemd/user/dsh-web.service
# Edit ~/.config/systemd/user/dsh-web.service placeholders
systemctl --user daemon-reload
systemctl --user enable --now dsh-web.service
systemctl --user status dsh-web.service   # should be active
```

## Step 7: Verify

```bash
# In your Hermes session:
/dsh-send test: write one sentence to the DSH workspace

# Expected:
# 1. A task appears on the board (hermes kanban --board dsh list)
# 2. DSH Web GUI (127.0.0.1:3080) auto-opens a session and executes
# 3. On completion, Hermes auto-pops 【外部通知】task xxx completed
```

## Patch conflict handling (version drift)

If `git apply` fails, your Hermes version differs from the patch baseline. Two options:

```bash
# Option A: 3-way apply (auto-merge)
git apply -3 hermes-external-event-steer.patch

# Option B: manual edit (patch is only ~104 lines, changes are clear)
#   cli.py: add _drain_done_notifications() + idle-loop call (2 spots)
#   config_defaults.py: add features section (1 spot)
# See hermes-side/PR-提交说明.md "改动文件" section for details.
```

## Common issues (known pitfalls)

1. **Plugin updates require a dsh web restart**: node does not hot-reload; after
   editing plugin code, `pkill -f "dsh web"` + restart.
2. **seen baseline timing**: done files already present when the done dir first
   appears are skipped (not replayed). When testing the notification chain, make
   sure the dir exists and is initialized, then write a NEW done file.
3. **SQLite lock**: Hermes and the watcher may both write kanban.db; the watcher
   retries (3 attempts) on busy.
4. **Serial execution**: only one task runs at a time; later tasks queue.
5. **Permission preset**: watcher sessions use danger-full-access
   (hermes-trusted); the security boundary relies on the Hermes-side whitelist —
   do not open it to untrusted task sources.
6. **Version pinning**: the plugin depends on `@deepseek-ai/dsh-*@0.1.0-rc.6`
   matching your DSH version. npm's `latest` dist-tag may point to an older
   version (0.0.1-rc.1), but the profile actually installs 0.1.0-rc.6 — install
   the plugin with `pnpm add file:` and it reuses the profile's existing deps.
