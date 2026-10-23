#!/usr/bin/env python3
"""PreToolUse hook (v1.110): only ONE session at a time may WRITE to the open editor.

Every writing UEFN MCP call takes (or renews) the lock Claude/logs/editor.lock for its session. If another session holds a
fresh lock (renewed less than TTL minutes ago) the call is denied with a plain message. Reading calls are never blocked.
The lock goes stale by itself, so a crashed session never blocks you for long.

  python Claude/hooks/editor_lock.py status      who holds the lock
  python Claude/hooks/editor_lock.py release     remove the lock (owner decision)
  UEFN_KIT_LOCK=0                                switch the lock off for a session

It never closes, kills or restarts anything. Any error inside the hook lets the call go through.
"""
import json
import os
import sys
import time

TTL = float(os.environ.get("UEFN_KIT_LOCK_TTL", "600"))  # seconds
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def lock_path(project):
    return os.path.join(project, "Claude", "logs", "editor.lock")


def read(project):
    try:
        return json.load(open(lock_path(project), encoding="utf-8"))
    except Exception:
        return None


def decide(project, sid, tool, now=None):
    """('allow'|'deny', reason). Takes or renews the lock when the call writes and nobody else holds it."""
    import editor_changes as ec
    now = now or time.time()
    if not ec.is_write(tool):
        return "allow", ""
    cur = read(project)
    if cur and cur.get("sid") and cur["sid"] != sid and now - float(cur.get("at", 0)) < TTL:
        mins = int((now - float(cur["at"])) // 60)
        return "deny", ("Another Claude session is writing to this editor (last write %d min ago, session %s). Two sessions writing at once "
                        "can undo each other. Wait for it, or the owner can run: python Claude/hooks/editor_lock.py release" % (mins, str(cur["sid"])[:8]))
    p = lock_path(project)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump({"sid": sid, "at": now, "tool": tool}, open(p, "w", encoding="utf-8"))
    return "allow", ""


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("status", "release"):
        proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        cur = read(proj)
        if sys.argv[1] == "status":
            if not cur:
                print("no lock")
            else:
                age = int(time.time() - float(cur.get("at", 0)))
                print("held by session %s, last write %ds ago (%s)" % (str(cur.get("sid"))[:8], age, "fresh" if age < TTL else "stale"))
            return 0
        if cur:
            try:
                os.remove(lock_path(proj))
                print("lock removed")
            except OSError:
                json.dump({"sid": "", "at": 0}, open(lock_path(proj), "w"))
                print("lock cleared")
        else:
            print("no lock")
        return 0
    try:
        if os.environ.get("UEFN_KIT_LOCK") == "0":
            return 0
        p = json.loads(sys.stdin.read() or "{}")
        ti = p.get("tool_input") or {}
        tool = str(ti.get("tool_name") or "")
        if not tool:
            return 0
        proj = os.environ.get("CLAUDE_PROJECT_DIR") or p.get("cwd") or os.getcwd()
        verdict, why = decide(proj, str(p.get("session_id") or ""), tool)
        if verdict == "deny":
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": why}}))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
