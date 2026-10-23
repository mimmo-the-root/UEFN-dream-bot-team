#!/usr/bin/env python3
"""PostToolUse hook: writes one line in Claude/logs/explore-ledger.jsonl for every UEFN MCP call made during real work
(src "work"). Successful calls arrive as PostToolUse, failed ones as PostToolUseFailure (field "error"); both are wired in settings.json, so recipes you really use become `proven` (recipes_status.py). Local only; nothing is sent anywhere.
Never blocks or fails a tool call: every error is swallowed and the exit code is always 0."""
import json
import os
import sys
import time


def clip_args(args, limit=400):
    """The arguments as JSON for the ledger. When they are longer than `limit` (a whole script, a long text), long strings are
    shortened to 60 characters so the JSON stays valid and keeps its names and booleans, which is all that proves a recipe."""
    s = json.dumps(args, ensure_ascii=False)
    if len(s) <= limit:
        return s

    def cut(v):
        if isinstance(v, str):
            return v[:60]
        if isinstance(v, dict):
            return {k: cut(x) for k, x in v.items()}
        if isinstance(v, list):
            return [cut(x) for x in v[:20]]
        return v
    s = json.dumps(cut(args), ensure_ascii=False)
    return s if len(s) <= 2000 else s[:2000]


def replay_on(logs):
    """A validation replay run by an agent creates Claude/logs/replay.on first and deletes it at the end: calls made meanwhile get
    src "replay" (the recipe was replayed on purpose with its own arguments), which counts as proof like real work. A marker older
    than 12 hours is ignored (forgotten)."""
    try:
        return time.time() - os.path.getmtime(os.path.join(logs, "replay.on")) < 12 * 3600
    except OSError:
        return False


def row_from_payload(p):
    ti = p.get("tool_input") or {}
    if not isinstance(ti, dict) or not ti.get("tool_name"):
        return None
    failed = p.get("hook_event_name") == "PostToolUseFailure" or (p.get("error") and "tool_response" not in p)
    resp = p.get("error") if failed else p.get("tool_response")
    text = resp if isinstance(resp, str) else json.dumps(resp, ensure_ascii=False, default=str)
    bad = bool(failed) or bool(isinstance(resp, dict) and (resp.get("isError") or resp.get("is_error") or resp.get("error")))
    low = text[:300].lower()
    if not bad and ('"iserror": true' in low or low.startswith("error") or '"error"' in low[:40]):
        bad = True
    rec = {"d": time.strftime("%Y-%m-%d"), "sid": str(p.get("session_id") or "")[:40], "t": time.strftime("%H:%M:%S"), "toolset": str(ti.get("toolset_name", ""))[:120], "tool": str(ti["tool_name"])[:120],
           "args": clip_args(ti.get("arguments") or {}), "r": "rejected" if bad else "ok",
           "src": "work", "peek": text[:200]}
    if bad:
        rec["why"] = text[:200]
    return rec


def main():
    try:
        p = json.loads(sys.stdin.read() or "{}")
        rec = row_from_payload(p)
        if not rec:
            return
        logs = os.path.join(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd(), "Claude", "logs")
        os.makedirs(logs, exist_ok=True)
        if replay_on(logs):
            rec["src"] = "replay"
        with open(os.path.join(logs, "explore-ledger.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    main()
    sys.exit(0)
