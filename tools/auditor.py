#!/usr/bin/env python3
"""Auditor prototype: approve or reject a replan (a new QUEUE.json) against plan.json.

Usage: auditor.py --plan plan.json --queue QUEUE.json [--result RESULT.json]

Rejects when the replan: drops an open plan item (neither queued nor excluded as owner-only),
queues an owner-only task, or exceeds 3 parallel (max_parallel or any wave larger than 3).
Writes a result JSON {"approved": bool, "reasons": [...]}; exit 0 approved, 1 rejected.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pm_queue import MAX_PARALLEL, is_owner_only  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def audit(plan, queue):
    reasons = []
    items = {it["id"]: it for it in plan.get("items", [])}
    entries = queue.get("queue", [])
    queued = [e.get("id") for e in entries]
    for pid, it in items.items():
        if pid not in queued and not is_owner_only(it):
            reasons.append("drops open item %s" % pid)
    for e in entries:
        it = items.get(e.get("id"), {"id": e.get("id"), "title": ""})
        if is_owner_only(it):
            reasons.append("queues owner-only task %s" % e.get("id"))
    if int(queue.get("max_parallel", 0) or 0) > MAX_PARALLEL:
        reasons.append("max_parallel %s exceeds %d" % (queue.get("max_parallel"), MAX_PARALLEL))
    waves = {}
    for e in entries:
        waves.setdefault(e.get("wave"), []).append(e.get("id"))
    for w, ids in sorted(waves.items(), key=lambda kv: str(kv[0])):
        if w is not None and len(ids) > MAX_PARALLEL:
            reasons.append("wave %s has %d parallel packages (max %d)" % (w, len(ids), MAX_PARALLEL))
    return {"approved": not reasons, "reasons": reasons or ["ok"]}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--plan", default=os.path.join(ROOT, "plan.json"))
    ap.add_argument("--queue", default=os.path.join(ROOT, "QUEUE.json"))
    ap.add_argument("--result", default=os.path.join(ROOT, "AUDIT-RESULT.json"))
    a = ap.parse_args(argv)
    with open(a.plan, "r", encoding="utf-8") as f:
        plan = json.load(f)
    with open(a.queue, "r", encoding="utf-8") as f:
        queue = json.load(f)
    res = audit(plan, queue)
    with open(a.result, "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=2)
        f.write("\n")
    print("%s: %s" % ("APPROVED" if res["approved"] else "REJECTED", "; ".join(res["reasons"])))
    return 0 if res["approved"] else 1


if __name__ == "__main__":
    sys.exit(main())
