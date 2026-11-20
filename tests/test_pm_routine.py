#!/usr/bin/env python3
"""Tests for tools/pm_routine.py with temp lab dirs only."""
import json, os, sys, tempfile
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(root, "tools"))
import pm_routine as pm

lab = tempfile.mkdtemp()
for d in ("inbox", "running", "done", "later"):
    os.makedirs(os.path.join(lab, "relay", d))
os.makedirs(os.path.join(lab, "logs"))
def w(p, t="x"):
    open(os.path.join(lab, p), "w").write(t)
w("relay/inbox/1-t-001-a.md"); w("relay/running/2-t-002-b.md"); w("relay/done/3-t-003-c.md")
for n in ("t-004", "t-005", "t-006", "t-007"):
    w("relay/later/9-%s-x.md" % n)
q = os.path.join(lab, "QUEUE.json")
json.dump({"queue": [{"id": "T-00%d" % i} for i in range(1, 8)]}, open(q, "w"))
w("logs/orchestrator.log", "2026 start T-005\n2026 start T-005\n2026 started T-005 again\n2026 start T-004\n")
hist = os.path.join(lab, "h.json")
json.dump([{"id": "T-006", "event": "start"}] * 3, open(hist, "w"))
now = 1000.0
w("logs/cod-activity.jsonl", "\n".join(json.dumps({"ts": t, "pkg": p}) for t, p in
  [(now, "a"), (now + 10, "a"), (now + 410, "a"), (now, "b"), (now + 30, "b"), "garbage"][:5]) + "\nnot json\n")

before = sorted(os.listdir(os.path.join(lab, "relay", "later")))
r = pm.routine(lab, q, hist)
assert r["free_slots"] == 1 and r["inbox"] == 1 and r["running"] == 1
assert sorted(l["id"] for l in r["LOOP"]) == ["T-005", "T-006"], r["LOOP"]
assert [x["id"] for x in r["requeue"]] == ["T-004"], r["requeue"]
assert [s["id"] for s in r["skipped"]] == ["T-007"]
assert r["idle"]["workers"]["a"]["idle_s"] == 400.0 and r["idle"]["workers"]["b"]["idle_gaps"] == 0
assert r["idle"]["mean_idle_s"] == 200.0, r["idle"]
assert sorted(os.listdir(os.path.join(lab, "relay", "later"))) == before, "read-only run changed files"
r = pm.routine(lab, q, hist, apply=True)
assert r["moved"] == ["9-t-004-x.md"]
assert os.path.exists(os.path.join(lab, "relay", "inbox", "9-t-004-x.md"))
assert len(os.listdir(os.path.join(lab, "relay", "later"))) == 3
r = pm.routine(lab, q, hist, apply=True)
assert r["free_slots"] == 0 and r["moved"] == []
empty = tempfile.mkdtemp()
r = pm.routine(empty, os.path.join(empty, "none.json"))
assert r["idle"]["present"] is False and r["requeue"] == []
print("ok")
