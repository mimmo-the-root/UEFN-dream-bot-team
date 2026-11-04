#!/usr/bin/env python3
"""Console button "Fix these tasks": turns a list of ROADMAP task ids into ONE relay command for Claude Code.
Only validated ids go in: each must be T-<3 digits>, exist in Claude/docs/ROADMAP.md and still be open. The command text is a fixed
template; no task text, path or free text from the page is ever copied into it.
Usage: python fix_request.py <project dir> [--dry] T-002 T-003      (prints one JSON line {"ok", "id", "file", "ids", "prompt"} or {"ok": false, "error"})"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OPEN = re.compile(r"^(to do|todo|in progress|blocked|da fare|in corso|bloccat\w*|wip)\b", re.I)
TEMPLATE = """id: {id}
title: Fix {n} roadmap task(s): {ids}
risk: medium
needs_owner: no
needs_mcp: no
parallel: no
do: |
  The owner pressed "Fix" on the console for these ROADMAP tasks: {ids}.
  Read each task in Claude/docs/ROADMAP.md (and the BUGS.md / AUDIT.md / PERFORMANCE.md entry named in its Source). Work on them one at a time, most serious first (major, then medium, then the rest).
  For each: set it In progress, make the change its acceptance criteria describe, run the checks (/verse-check and the review gates of the kit), and have planner-docs mark it Done only after the reviewers pass.
  Stop at the first task that fails twice, say which one and why, and leave the rest To do. Do not start any task that is not in this list.
report: for each task id: done, failed (why) or not started; then one line on what to test in play.
"""


def _tasks(project):
    """Every task row of ROADMAP.md, also those after a blank line or a comment (real tables are often grouped by hand)."""
    p = os.path.join(project, "Claude", "docs", "ROADMAP.md")
    if not os.path.isfile(p):
        return {}
    head = None
    out = {}
    for line in open(p, encoding="utf-8", errors="replace").read().replace("\r\n", "\n").split("\n"):
        if head is None and re.match(r"^\|\s*ID\s*\|", line, re.I) and re.search(r"\|\s*Feature\s*\|", line, re.I):  # not the Phases table, which also starts with ID
            head = [c.strip().lower() for c in line.strip().strip("|").split("|")]
        elif head and re.match(r"^\|\s*T-\d{3}\s*\|", line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            out[cells[0]] = dict(zip(head, cells))
    return out


def _next_id(rdir):
    n = 0
    for sub in ("inbox", "running", "done", "outbox", "_moved"):
        d = os.path.join(rdir, sub)
        if os.path.isdir(d):
            for f in os.listdir(d):
                m = re.match(r"^\.?(\d{3,})", f)
                if m:
                    n = max(n, int(m.group(1)))
    return "%03d" % (n + 1)


def enqueue(project, ids, dry=False):
    if not isinstance(ids, (list, tuple)) or not ids:
        return {"ok": False, "error": "no task ids given"}
    if any(not isinstance(i, str) or not re.fullmatch(r"T-\d{3}", i) for i in ids):
        return {"ok": False, "error": "only task ids like T-012 are accepted"}
    ids = sorted(set(ids))
    tasks = _tasks(project)
    for i in ids:
        if i not in tasks:
            return {"ok": False, "error": "%s is not in ROADMAP.md" % i}
        if not OPEN.match(tasks[i].get("status", "")):
            return {"ok": False, "error": "%s is not open (status: %s)" % (i, tasks[i].get("status", ""))}
    rdir = os.path.join(project, "Claude", "relay")
    if not os.path.isdir(os.path.join(rdir, "inbox")):
        return {"ok": False, "error": "no relay folder in this project (Claude/relay/inbox): copy the text instead"}
    cid = _next_id(rdir)
    text = TEMPLATE.format(id=cid, n=len(ids), ids=", ".join(ids))
    res = {"ok": True, "id": cid, "ids": ids, "prompt": text}
    if dry:
        return res
    name = "%s-fix-tasks.md" % cid
    inbox = os.path.join(rdir, "inbox")
    tmp = os.path.join(inbox, "." + cid + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, os.path.join(inbox, name))
    res["file"] = name
    return res


if __name__ == "__main__":
    a = sys.argv[1:]
    dry = "--dry" in a
    a = [x for x in a if x != "--dry"]
    print(json.dumps(enqueue(a[0], a[1:], dry=dry) if a else {"ok": False, "error": "usage"}))
