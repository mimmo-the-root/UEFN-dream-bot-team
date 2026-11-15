"""relay_plan.py: finished agents are closed first, parallel commands fill up to 5 slots, after: waits, one serial at a time."""
import os, sys, tempfile
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(root, "project-template", "Claude", "hooks"))
import relay_plan as rp
r = tempfile.mkdtemp()
for d in ("inbox", "running", "done", "outbox"):
    os.makedirs(os.path.join(r, d))
def cmd(folder, name, parallel="yes", after="", approved="yes"):
    open(os.path.join(r, folder, name), "w").write("id: %s\ntitle: t\nrisk: low\nneeds_owner: no\nparallel: %s\n%sapproved: %s\ndo: x\n" % (name[:3], parallel, ("after: %s\n" % after) if after else "", approved))
cmd("done", "001-a.md")
for i in range(2, 5):
    cmd("running", "%03d-r.md" % i)
open(os.path.join(r, "outbox", "002-r.result.md"), "w").write("ok")
for i in range(10, 16):
    cmd("inbox", "%03d-p.md" % i)
cmd("inbox", "020-s.md", parallel="no")
cmd("inbox", "021-w.md", after="001, 099")
p = rp.plan(r)
assert p["close"] == ["002-r.md"] and p["active"] == ["003-r.md", "004-r.md"], p
assert p["start"] == ["010-p.md", "011-p.md", "012-p.md"], "5 slots minus 2 running"
assert p["run_now"] == "020-s.md" and any(w.startswith("021-w.md: after 099") for w in p["waiting"]), p
open(os.path.join(r, "STOP"), "w").write("x")
assert rp.plan(r)["start"] == [] and rp.plan(r)["run_now"] is None
print("ok relay_plan")
