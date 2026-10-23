"""Economy simulator: milestones, flags, init never overwrites."""
import json, os, shutil, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "user-level-hooks"))
import economy_sim as e
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
cfg = {"session_minutes": 10, "base_income_per_sec": 1, "generators": [{"name": "A", "base_cost": 10, "growth": 1.1, "income": 1, "max": 5}],
       "targets": [{"name": "early", "cost": 5}, {"name": "mid", "cost": 300}, {"name": "far", "cost": 10 ** 9}]}
r = e.simulate(cfg, horizon=3600)
t = {x["name"]: x["t"] for x in r["targets"]}
ok(t["early"] == 5, "base income reaches a small milestone at the expected second")
ok(t["mid"] is not None and t["mid"] < 300, "buying a generator speeds the milestone up")
ok(t["far"] is None, "unreachable milestone stays None")
ok(r["generators"][0]["owned"] == 5, "generator stops at max")
fl = e.verdicts(cfg, r)
ok(any("far" in f and "not reached" in f for f in fl), "unreachable milestone is flagged")
ok(not any("'early'" in f for f in fl), "first milestone is allowed to be early")
d = tempfile.mkdtemp()
try:
    p = os.path.join(d, "docs", "economy.json")
    ok(e.main(["init", p]) == 0 and os.path.isfile(p), "init writes an example")
    ok(e.main(["init", p]) == 1, "init never overwrites")
    ok(e.main(["run", p]) in (0, 1), "run works on the example")
finally:
    shutil.rmtree(d, ignore_errors=True)
