#!/usr/bin/env python3
"""What the agents changed in the open editor, session by session, and a plan to undo it (v1.110).

Reads Claude/logs/explore-ledger.jsonl (one line per UEFN MCP call, written by mcp_work_log.py) and keeps the calls that WRITE
(create, spawn, add, set, move, delete, ...). Reading calls (Get, List, Find, Describe, Capture...) are ignored.

  python Claude/hooks/editor_changes.py list [--last N] [--session ID]   sessions and the writes of the chosen one (default: the newest)
  python Claude/hooks/editor_changes.py undo-plan [--session ID]         the steps that would undo that session, newest first

This script NEVER touches the editor. `undo-plan` only writes a plan: a creation can be undone by deleting what it created; a change
of a value, a move or a rename cannot (the old value was not recorded): for those the plan says "manual" (the editor's own Undo,
or a restore point for Verse code: safety_net.py). Whoever runs the plan (an agent) keeps the lab rules (mcp_lab.py) and asks the
owner before any deletion in a real project.
"""
import json
import os
import re
import sys

READ_WORDS = re.compile(r"^(Get|List|Find|Is|Has|Query|Search|Read|Describe|Capture|Count|Check|Validate|Resolve|Preview|Show|Fetch|Lookup|Select|Open|Load)", re.I)
CREATE_WORDS = re.compile(r"^(Create|Spawn|Add|Duplicate|Import|New|Make|Place|Build|Instantiate|Clone)", re.I)
DELETE_WORDS = re.compile(r"^(Delete|Remove|Destroy|Clear)", re.I)


def is_write(tool):
    """Name-based guess (the tool map's readOnly flag is not always available offline)."""
    return bool(tool) and not READ_WORDS.match(tool)


def load(project):
    p = os.path.join(project, "Claude", "logs", "explore-ledger.jsonl")
    rows = []
    if os.path.isfile(p):
        for l in open(p, encoding="utf-8", errors="replace"):
            try:
                rows.append(json.loads(l))
            except ValueError:
                pass
    return rows


def writes(rows):
    return [r for r in rows if r.get("src") in ("work", "replay") and r.get("r") == "ok" and is_write(r.get("tool", ""))]


def sessions(rows):
    """[(sid, [write rows])] oldest first. Rows without a session id are grouped by date."""
    out, order = {}, []
    for r in writes(rows):
        k = r.get("sid") or ("day-" + (r.get("d") or "unknown"))
        if k not in out:
            out[k] = []
            order.append(k)
        out[k].append(r)
    return [(k, out[k]) for k in order]


def paths_of(row):
    try:
        a = json.loads(row.get("args") or "{}")
    except ValueError:
        return []
    found = []

    def walk(v):
        if isinstance(v, str) and re.match(r"^/[A-Za-z0-9_/.\-]+", v) and len(v) < 300:
            found.append(v)
        elif isinstance(v, dict):
            [walk(x) for x in v.values()]
        elif isinstance(v, list):
            [walk(x) for x in v[:30]]
    walk(a)
    return found


def plan(session_rows):
    """Newest first. action: delete (undo a creation) | manual (cannot be undone from the record) | skip (already a deletion)."""
    steps = []
    for r in reversed(session_rows):
        tool, ps = r.get("tool", ""), paths_of(r)
        if CREATE_WORDS.match(tool) and ps:
            steps.append({"action": "delete", "of": "%s.%s" % (r.get("toolset", ""), tool), "paths": ps[:3], "at": r.get("t", ""),
                          "note": "delete what this call created (ask the owner first in a real project; only inside the lab rules)"})
        elif DELETE_WORDS.match(tool):
            steps.append({"action": "manual", "of": "%s.%s" % (r.get("toolset", ""), tool), "paths": ps[:3], "at": r.get("t", ""),
                          "note": "a deletion cannot be redone from the record: use the editor's Undo or source control"})
        else:
            steps.append({"action": "manual", "of": "%s.%s" % (r.get("toolset", ""), tool), "paths": ps[:3], "at": r.get("t", ""),
                          "note": "the old value was not recorded: use the editor's Undo, or fix by hand"})
    return steps


def pick(rows, sid=None):
    ss = sessions(rows)
    if not ss:
        return None, []
    if sid:
        for k, v in ss:
            if k == sid or k.startswith(sid):
                return k, v
        return None, []
    return ss[-1]


def main(argv):
    if not argv or argv[0] not in ("list", "undo-plan"):
        print(__doc__)
        return 2
    args = [a for a in argv[1:] if not a.startswith("--")]
    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    def opt(n, d=None):
        return argv[argv.index(n) + 1] if n in argv and argv.index(n) + 1 < len(argv) else d
    rows = load(proj)
    sid = opt("--session")
    if argv[0] == "list":
        ss = sessions(rows)
        if not ss:
            print("no editor writes recorded yet (the ledger is empty or only has reading calls)")
            return 0
        n = int(opt("--last", 5))
        for k, v in ss[-n:]:
            print("session %-12s %3d write(s)  %s" % (k[:12], len(v), (v[0].get("d", "") + " " + v[0].get("t", "")).strip()))
        k, v = pick(rows, sid)
        if not k:
            print("session %s not found" % sid)
            return 1
        print("\nwrites of session %s:" % k[:12])
        for r in v:
            print("  %s %s.%s %s" % (r.get("t", ""), r.get("toolset", ""), r.get("tool", ""), " ".join(paths_of(r)[:2])))
        return 0
    k, v = pick(rows, sid)
    if not k:
        print("nothing to undo: no recorded writes" + (" for session %s" % sid if sid else ""))
        return 0
    steps = plan(v)
    print("UNDO PLAN for session %s (%d writes, newest first). Nothing was changed." % (k[:12], len(steps)))
    for i, s in enumerate(steps, 1):
        print("  %d. [%s] %s %s  (%s)" % (i, s["action"], s["of"], " ".join(s["paths"]), s["note"]))
    d = sum(1 for s in steps if s["action"] == "delete")
    print("%d step(s) can be undone by deleting what was created; %d need the editor's Undo or a restore point." % (d, len(steps) - d))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
