#!/usr/bin/env bash
# restart-web.sh — 重启 dsh web 以加载插件变更（v2：杀干净再启，防 singleton lock 冲突自杀）
set -u
LOG=/tmp/dsh-restart.log
echo "=== restart $(date) ===" >> "$LOG"

# 1) 等待当前回合收尾（给用户读完提示的时间）
sleep 20

# 2) 杀干净旧 web host：pkill node + bash 包装，然后等进程死透（最多 20s）
pkill -f "dsh web --port 3080" 2>/dev/null >> "$LOG" || true
for i in $(seq 1 10); do
  if ! pgrep -f "dsh web --port 3080" >/dev/null 2>&1; then break; fi
  echo "waiting old web to die... ($i)" >> "$LOG"
  sleep 2
done
if pgrep -f "dsh web --port 3080" >/dev/null 2>&1; then
  echo "FATAL: old web still alive, killing -9" >> "$LOG"
  pkill -9 -f "dsh web --port 3080" 2>/dev/null || true
  sleep 2
fi
echo "old web confirmed dead" >> "$LOG"

# 3) 等端口释放（最多 10s）
for i in $(seq 1 5); do
  if ! ss -tln 2>/dev/null | grep -q ':3080 '; then break; fi
  echo "port 3080 still busy, waiting..." >> "$LOG"
  sleep 2
done

# 4) 残留锁清理：holder 已死的锁由 watcher 自身 PID 存活检查回收，无需手动删；
#    但确认触发目录在
mkdir -p $DSH_TRIGGER_DIR

# 5) 启动新 web（脱离会话，日志到 /tmp/dsh-web.log）
export HOME=$HOME
nohup $DSH_BIN web --port 3080 > /tmp/dsh-web.log 2>&1 < /dev/null &
NEWPID=$!
disown "$NEWPID" 2>/dev/null || true

# 6) 健康检查：等端口起来（最多 20s），失败则重试一次
ok=0
for i in $(seq 1 10); do
  sleep 2
  if ss -tln 2>/dev/null | grep -q ':3080 '; then ok=1; break; fi
done
if [ "$ok" = "1" ]; then
  echo "OK: web up on :3080 (pid $NEWPID)" >> "$LOG"
else
  echo "WARN: port 3080 not up, killing and retrying once" >> "$LOG"
  kill "$NEWPID" 2>/dev/null || true
  sleep 2
  pkill -f "dsh web --port 3080" 2>/dev/null || true
  sleep 2
  nohup $DSH_BIN web --port 3080 > /tmp/dsh-web.log 2>&1 < /dev/null &
  echo "retry launched pid $!" >> "$LOG"
fi
echo "=== restart script finished $(date) ===" >> "$LOG"
