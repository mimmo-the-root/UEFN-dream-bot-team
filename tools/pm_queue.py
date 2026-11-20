#!/usr/bin/env python3
"""Product-Manager prototype: read plan.json (tools/plan_json.py) and write QUEUE.json.

Usage: pm_queue.py [--plan PATH] [--out PATH] [--result PATH]

Order: release (P0-R3 < P0-R11 < Later), then priority (P0 < P1 < P2), then id.
Owner-only tasks (T-027, T-044, T-070 version bump, T-071, T-117, and any "[Owner]" title)
are never queued; they are listed under "excluded". Packages get a "wave" number; at most
MAX_PARALLEL packages share a wave. Reads plan.json only, never the Lab.
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAX_PARALLEL = 3
OWNER_ONLY = ("T-027", "T-044", "T-070", "T-071", "T-117")


def is_owner_only(item):
    return item.get("id") in OWNER_ONLY or str(item.get("title", "")).lstrip().lower().startswith("[owner]")


def _num(text, pat):
    m = re.search(pat, str(text))
    return int(m.group(1)) if m else 10 ** 6


def sort_key(item):
    rel = item.get("release", "")
    return (_num(rel, r"R(\d+)"), _num(item.get("priority", ""), r"P(\d+)"), _num(item.get("id", ""), r"(\d+)"))


def build_queue(plan):
    queue, excluded = [], []
    for it in sorted(plan.get("items", []), key=sort_key):
        if is_owner_only(it):
            excluded.append({"id": it["id"], "reason": "owner-only task"})
            continue
        queue.append({"id": it["id"], "release": it.get("release", ""),
                      "reason": "open %s item in %s (%s)" % (it.get("priority") or "unprioritized",
                                                          it.get("release") or "no release",
                                                          str(it.get("status", ""))[:40])})
    for n, q in enumerate(queue):
        q["wave"] = n // MAX_PARALLEL + 1
    return {"max_parallel": MAX_PARALLEL, "count": len(queue), "queue": queue, "excluded": excluded}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--plan", default=os.path.join(ROOT, "plan.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "QUEUE.json"))
    ap.add_argument("--result", default="")
    a = ap.parse_args(argv)
    with open(a.plan, "r", encoding="utf-8") as f:
        queue = build_queue(json.load(f))
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)
        f.write("\n")
    if a.result:
        with open(a.result, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"tool": "pm_queue", "ok": True, "queued": queue["count"],
                       "excluded": len(queue["excluded"]), "out": a.out}, f, indent=2)
            f.write("\n")
    print("wrote %s (%d queued, %d excluded)" % (a.out, queue["count"], len(queue["excluded"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
