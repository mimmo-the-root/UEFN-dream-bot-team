#!/usr/bin/env python3
"""Tests for tools/pm_queue.py and tools/auditor.py on temp files only."""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PM = os.path.join(ROOT, "tools", "pm_queue.py")
AU = os.path.join(ROOT, "tools", "auditor.py")
fails = []


def check(name, cond):
    if not cond:
        fails.append(name)
        print("FAIL " + name)


def run(tool, *args):
    return subprocess.run([sys.executable, tool] + list(args), capture_output=True, text=True)


def it(i, rel="P0-R3", pri="P1", title="[Pkg] x"):
    return {"id": i, "title": title, "command": "c", "status": "To do", "priority": pri, "release": rel}


PLAN = {"items": [it("T-005", "P0-R11"), it("T-002", "Later"), it("T-001"), it("T-003", pri="P0"),
                  it("T-004"), it("T-027"), it("T-044"), it("T-070"), it("T-071"), it("T-117"),
                  it("T-200", title="[Owner] switch on")]}


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


with tempfile.TemporaryDirectory() as d:
    plan, q, res, ares = [os.path.join(d, n) for n in ("plan.json", "QUEUE.json", "pm.json", "audit.json")]
    with open(plan, "w") as f:
        json.dump(PLAN, f)
    r = run(PM, "--plan", plan, "--out", q, "--result", res)
    check("pm exit 0", r.returncode == 0)
    Q = load(q)
    ids = [e["id"] for e in Q["queue"]]
    check("order", ids == ["T-003", "T-001", "T-004", "T-005", "T-002"])
    check("no owner-only", not set(ids) & {"T-027", "T-044", "T-070", "T-071", "T-117", "T-200"})
    check("excluded listed", len(Q["excluded"]) == 6)
    check("entry fields", all(e["reason"] and e["release"] and e["id"] for e in Q["queue"]))
    check("max 3 per wave", max(sum(1 for e in Q["queue"] if e["wave"] == w) for w in {e["wave"] for e in Q["queue"]}) <= 3)
    check("pm result file", load(res)["ok"] is True)
    # approve
    r = run(AU, "--plan", plan, "--queue", q, "--result", ares)
    check("auditor approves", r.returncode == 0 and load(ares)["approved"] is True)
    # drop an item
    bad = json.loads(json.dumps(Q))
    bad["queue"] = [e for e in bad["queue"] if e["id"] != "T-004"]
    bp = os.path.join(d, "bad1.json")
    json.dump(bad, open(bp, "w"))
    r = run(AU, "--plan", plan, "--queue", bp, "--result", ares)
    check("rejects drop", r.returncode == 1 and any("T-004" in x for x in load(ares)["reasons"]))
    # owner-only added
    bad = json.loads(json.dumps(Q))
    bad["queue"].append({"id": "T-117", "release": "P0-R3", "reason": "x", "wave": 3})
    bp = os.path.join(d, "bad2.json")
    json.dump(bad, open(bp, "w"))
    r = run(AU, "--plan", plan, "--queue", bp, "--result", ares)
    check("rejects owner-only", r.returncode == 1 and any("owner-only" in x for x in load(ares)["reasons"]))
    # over parallel
    bad = json.loads(json.dumps(Q))
    bad["max_parallel"] = 4
    for e in bad["queue"]:
        e["wave"] = 1
    bp = os.path.join(d, "bad3.json")
    json.dump(bad, open(bp, "w"))
    r = run(AU, "--plan", plan, "--queue", bp, "--result", ares)
    reasons = load(ares)["reasons"]
    check("rejects parallel", r.returncode == 1 and any("max_parallel" in x for x in reasons) and any("wave 1" in x for x in reasons))

if fails:
    print("%d failed" % len(fails))
    sys.exit(1)
print("ok test_pm_auditor")
