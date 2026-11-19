#!/usr/bin/env python3
"""Cod activity hook: appends one JSON line per event to Claude/logs/cod-activity.jsonl, so the watchdog (tools/watchdog.py)
and the planner can tell from FILES whether Cod is working, idle or blocked, without reading its terminal.

Line fields: time (local ISO seconds), ts (epoch), event, tool, ok (true/false), blocked (true/false), reason (first 200 chars,
only for a permission denial or classifier block), pkg (package id from env UEFN_PACKAGE_ID / COD_PACKAGE_ID / CLAUDE_PACKAGE_ID,
else the newest file in relay/running, else "").
The file is capped at 2000 lines (the newest are kept).

Claude Code events (checked against https://code.claude.com/docs/en/hooks, 33 events listed):
  Wire these (all exist): PostToolUse, PostToolUseFailure, Stop, SubagentStop, Notification, PermissionDenied.
  Events that do NOT exist and must not be wired: none of the six requested ones is missing.
  (PermissionRequest and StopFailure exist too but are not used here.)

Never fails, never blocks, never prints to stdout: every error is swallowed and the exit code is always 0.
Set UEFN_COD_ACTIVITY=0 to switch it off. Stdlib only.
"""
import json
import os
import sys
import time

CAP = 2000
BLOCK_WORDS = ("permission", "denied", "classifier", "blocked by", "not allowed", "auto mode", "was blocked", "refused by")


def lab_dir():
    d = os.environ.get("UEFN_LAB") or os.path.join(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd(), "Claude")
    return d


def package_id(lab):
    for k in ("UEFN_PACKAGE_ID", "COD_PACKAGE_ID", "CLAUDE_PACKAGE_ID"):
        if os.environ.get(k):
            return os.environ[k][:80]
    try:
        run = os.path.join(lab, "relay", "running")
        files = [os.path.join(run, n) for n in os.listdir(run) if os.path.isfile(os.path.join(run, n))]
        if files:
            return os.path.splitext(os.path.basename(max(files, key=os.path.getmtime)))[0][:80]
    except Exception:
        pass
    return ""


def text_of(v):
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    try:
        return json.dumps(v, ensure_ascii=False)
    except Exception:
        return str(v)


def build_row(p, lab, now=None):
    now = time.time() if now is None else now
    ev = str(p.get("hook_event_name") or p.get("event") or "")
    tool = str(p.get("tool_name") or "")
    ok, blocked, reason = True, False, ""
    if ev == "PermissionDenied":
        ok, blocked = False, True
        reason = text_of(p.get("reason") or p.get("message") or p.get("error") or "permission denied")
    elif ev == "PostToolUseFailure":
        ok = False
        err = text_of(p.get("error") or p.get("tool_response"))
        if any(w in err.lower() for w in BLOCK_WORDS):
            blocked, reason = True, err
    elif ev == "PostToolUse":
        resp = p.get("tool_response")
        if isinstance(resp, dict) and (resp.get("is_error") or resp.get("error")):
            ok = False
            err = text_of(resp.get("error") or resp.get("content") or resp)
            if any(w in err.lower() for w in BLOCK_WORDS):
                blocked, reason = True, err
    elif ev == "Notification":
        msg = text_of(p.get("message"))
        if "permission" in msg.lower():
            reason = msg
    return {"time": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now)), "ts": int(now), "event": ev, "tool": tool,
            "ok": ok, "blocked": blocked, "reason": " ".join(reason.split())[:200], "pkg": package_id(lab)}


def append_capped(path, row, cap=CAP):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with open(path, "rb") as f:
        data = f.read()
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    if len(lines) > cap:
        tmp = path + ".tmp"
        with open(tmp, "wb") as f:
            f.write(b"\n".join(lines[-cap:]) + b"\n")
        os.replace(tmp, path)


def main():
    try:
        if os.environ.get("UEFN_COD_ACTIVITY") == "0":
            return
        raw = sys.stdin.read()
        p = json.loads(raw) if raw.strip() else {}
        if not isinstance(p, dict) or not (p.get("hook_event_name") or p.get("event")):
            return
        lab = lab_dir()
        append_capped(os.path.join(lab, "logs", "cod-activity.jsonl"), build_row(p, lab))
    except Exception:
        pass


if __name__ == "__main__":
    main()
    sys.exit(0)
