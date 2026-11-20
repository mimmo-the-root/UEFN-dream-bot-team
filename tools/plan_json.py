#!/usr/bin/env python3
"""Build plan.json from docs/ROADMAP.md (read-only) and gate it.

Usage:
  plan_json.py build [--roadmap PATH] [--out PATH]   write plan.json
  plan_json.py check [--roadmap PATH]                exit 1 if an open item lacks id/command/status

Row format: | ID | Feature | Status | Acceptance | Priority | Release | Kind | Source |
An item is open when its status does not start with "Done".
Command: the first `backticked` test command in the acceptance (python/pytest/bash/node/sh),
otherwise the acceptance text itself.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ID_RE = re.compile(r"^T-\d+$")
CMD_RE = re.compile(r"`((?:python3?|pytest|bash|sh|node)\b[^`]*)`")


def default_roadmap():
    return os.path.join(ROOT, "docs", "ROADMAP.md")


def parse_rows(text):
    """Return a list of dicts for every table row whose first cell looks like T-NNN."""
    rows = []
    for line in text.replace("\r\n", "\n").split("\n"):
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells or not ID_RE.match(cells[0]) or len(cells) < 4:
            continue
        # fixed: ID, Feature, Status, then Acceptance (may contain '|'), then 4 trailing columns
        tail = cells[-4:] if len(cells) >= 8 else []
        acc_cells = cells[3:-4] if len(cells) >= 8 else cells[3:]
        rows.append({
            "id": cells[0],
            "title": cells[1],
            "status": cells[2],
            "acceptance": " | ".join(acc_cells).strip(),
            "priority": tail[0] if tail else "",
            "release": tail[1] if tail else "",
            "kind": tail[2] if tail else "",
        })
    return rows


def is_open(row):
    return not row["status"].lower().startswith("done")


def build_plan(text):
    items = []
    for r in parse_rows(text):
        if not is_open(r):
            continue
        m = CMD_RE.search(r["acceptance"])
        command = m.group(1).strip() if m else r["acceptance"]
        items.append({"id": r["id"], "title": r["title"], "command": command,
                      "status": r["status"], "priority": r["priority"], "release": r["release"]})
    return {"source": "docs/ROADMAP.md", "count": len(items), "items": items}


def check_plan(plan):
    errs = []
    for i, it in enumerate(plan["items"]):
        for key in ("id", "command", "status"):
            if not str(it.get(key, "")).strip():
                errs.append("item %d (%s): missing %s" % (i, it.get("id") or "?", key))
    return errs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("mode", choices=["build", "check"])
    ap.add_argument("--roadmap", default=default_roadmap())
    ap.add_argument("--out", default=os.path.join(ROOT, "plan.json"))
    a = ap.parse_args(argv)
    with open(a.roadmap, "r", encoding="utf-8", newline="") as f:
        plan = build_plan(f.read())
    errs = check_plan(plan)
    if a.mode == "check":
        for e in errs:
            print("FAIL " + e)
        print("%d open items, %d problems" % (plan["count"], len(errs)))
        return 1 if errs else 0
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("wrote %s (%d open items)" % (a.out, plan["count"]))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
