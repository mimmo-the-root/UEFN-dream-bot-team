#!/usr/bin/env python3
"""PostToolUse hook: writes one line in Claude/logs/explore-ledger.jsonl for every UEFN MCP call made during real work
(src "work"). Successful calls arrive as PostToolUse, failed ones as PostToolUseFailure (field "error"); both are wired in settings.json, so recipes you really use become `proven` (recipes_status.py). Local only; nothing is sent anywhere.
Never blocks or fails a tool call: every error is swallowed and the exit code is always 0."""
import json
import os
import sys
import time


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
    rec = {"t": time.strftime("%H:%M:%S"), "toolset": str(ti.get("toolset_name", ""))[:120], "tool": str(ti["tool_name"])[:120],
           "args": json.dumps(ti.get("arguments") or {}, ensure_ascii=False)[:400], "r": "rejected" if bad else "ok",
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
        with open(os.path.join(logs, "explore-ledger.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


if __name__ == "__main__":
    main()
    sys.exit(0)
