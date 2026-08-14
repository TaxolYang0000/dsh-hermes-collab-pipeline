#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从会话 jsonl 中提取指定轮次的完整会话（用户消息、助手回复含思考、工具调用/结果），
输出为可读 markdown 文本。

用法: python3 extract_turns.py <session.jsonl> <turn_start> <turn_end> <output.md>
按行区间提取（行号从 1 开始）。
"""
import json
import sys
import datetime


def ts_to_str(ms):
    return datetime.datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d %H:%M:%S")


def text_of(items):
    """从 content 数组中提取纯文本。"""
    if items is None:
        return ""
    if isinstance(items, str):
        return items
    out = []
    for c in items:
        if not isinstance(c, dict):
            continue
        t = c.get("type")
        if t == "text" and c.get("text"):
            out.append(c["text"])
        elif t == "tool-result":
            inner = text_of(c.get("content"))
            if inner:
                out.append(f"[工具结果]\n{inner}")
    return "\n".join(out)


def reasoning_of(items):
    if not isinstance(items, list):
        return ""
    out = []
    for c in items:
        if isinstance(c, dict) and c.get("type") == "reasoning" and c.get("text"):
            out.append(c["text"])
    return "\n".join(out)


def main():
    src, start, end, dst = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    lines = open(src, encoding="utf-8").read().splitlines()
    out = []
    for i in range(start - 1, min(end, len(lines))):
        try:
            rec = json.loads(lines[i])
        except Exception as ex:
            out.append(f"> 行 {i+1} 解析失败: {ex}\n```\n{lines[i][:500]}\n```\n")
            continue
        typ = rec.get("type")
        data = rec.get("data") or {}
        time = rec.get("time")
        tstr = ts_to_str(time) if isinstance(time, (int, float)) else ""
        seq = rec.get("seq", "?")

        if typ == "user/message":
            src_kind = data.get("source", {}).get("kind", "?")
            body = text_of(data.get("content"))
            if src_kind == "plugin":
                body = f"(系统注入, form={data.get('source', {}).get('form')})\n{body[:2000]}"
            out.append(f"## 🧑 用户消息 [seq {seq}] ({tstr})\n\n{body}\n")
        elif typ == "assistant/message":
            msg = data.get("message") or {}
            reas = reasoning_of(msg.get("content"))
            body = text_of(msg.get("content"))
            if reas:
                out.append(f"## 🤖 助手回复 [seq {seq}] ({tstr})\n\n<details><summary>思考过程</summary>\n\n{reas}\n\n</details>\n\n### 回复正文\n\n{body}\n")
            else:
                out.append(f"## 🤖 助手回复 [seq {seq}] ({tstr})\n\n{body}\n")
        elif typ == "tool/call":
            args = data.get("arguments") or "{}"
            try:
                args = json.dumps(json.loads(args), ensure_ascii=False, indent=2)
            except Exception:
                pass
            out.append(f"## 🔧 工具调用 [seq {seq}] ({tstr})\n\n**{data.get('name')}**\n```json\n{args}\n```\n")
        elif typ == "tool/result":
            msg = data.get("message") or {}
            body = text_of(msg.get("content"))
            is_err = ""
            for c in (msg.get("content") or []):
                if isinstance(c, dict) and c.get("isError"):
                    is_err = " (ERROR)"
            out.append(f"## 📥 工具结果 [seq {seq}] ({tstr}){is_err}\n\n```\n{body[:8000]}\n```\n")
        elif typ in ("turn/start",):
            out.append(f"# 🟢 第 {data.get('turn')} 轮开始 ({tstr})\n")
        elif typ in ("turn/end",):
            reason = data.get("reason", {})
            out.append(f"# 🔴 第 {data.get('turn')} 轮结束 ({tstr}) 原因: {json.dumps(reason, ensure_ascii=False)[:300]}\n")
        # 其他类型（chunk/step/request 等）忽略
    with open(dst, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"已提取行 {start}-{end} -> {dst} ({len(out)} 条记录)")


if __name__ == "__main__":
    main()
