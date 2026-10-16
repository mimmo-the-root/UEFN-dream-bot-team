"""recipes_status.py: proven-by-use evidence from the ledger (offline, temp files)."""
import json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "project-template", "Claude", "hooks"))
import recipes_status as R

fails = []
def check(n, c):
    print(("PASS " if c else "FAIL ") + n)
    if not c: fails.append(n)

recipes = {"A.B/Make": {"args": {"folderPath": "{lab_mount}/X", "name": "N", "opts": {"refPath": "{p}"}, "flag": True}, "status": "verified"},
           "A.B/Make#v2": {"args": {"name": "N"}, "status": "verified"},
           "A.B/Other": {"args": {"x": 1}, "status": "unverified"}}
with tempfile.TemporaryDirectory() as d:
    led = os.path.join(d, "explore-ledger.jsonl")
    rows = [
        {"toolset": "A.B", "tool": "Make", "r": "ok", "args": json.dumps({"folderPath": "/g/p/UI", "name": "WBP_1", "opts": {"refPath": "/Script/X"}, "flag": True}), "src": "work"},
        {"toolset": "A.B", "tool": "Make", "r": "ok", "src": "work", "args": json.dumps({"folderPath": "/g/p/UI", "name": "WBP_2", "opts": {"refPath": "/Script/X"}, "flag": False})},
        {"toolset": "A.B", "tool": "Make", "r": "rejected", "src": "work", "why": "bad path /g/p/UI/x", "args": json.dumps({"name": "N"})},
        {"toolset": "A.B", "tool": "Other", "r": "ok", "args": json.dumps({"x": 5}), "src": "battery"},
        {"toolset": "A.B", "tool": "Other", "r": "ok", "args": json.dumps({"x": 5, "p": "/G/Cover/Cover_1"})},
        {"toolset": "A.B", "tool": "Other", "r": "ok", "src": "work", "args": '{"x": 5, "cut'},
        {"toolset": "A.B", "tool": "Make", "r": "ok", "args": json.dumps({"folderPath": "/g/p/UI", "name": "N3", "opts": {"refPath": "/Script/X"}, "flag": True})},
    ]
    open(led, "w").write("\n".join(json.dumps(r) for r in rows))
    m = R.merge(recipes, R.evidence_from_ledger(led))
    check("same call form is proven (values ignored); a lab row without src work is not counted", m["A.B/Make"]["status"] == "proven" and m["A.B/Make"]["ok"] == 1)
    check("a different boolean is a different form", m["A.B/Make"]["ok"] == 1)
    check("a failed call is counted, not proven", m["A.B/Make#v2"]["status"] == "tool-ok" and m["A.B/Make#v2"]["failed"] == 1 and "bad path" in m["A.B/Make#v2"]["last_failure"])
    check("only src work counts: lab/agent rows, battery rows and cut calls never prove", m["A.B/Other"]["status"] == "unverified" and m["A.B/Other"]["ok"] == 0)
    check("verified is shown as tool-ok", R.merge({"k": {"args": {}, "status": "verified"}}, {})["k"]["status"] == "tool-ok")
    ex = R.export(m)
    txt = json.dumps(ex)
    check("export has counts only: no args, no paths", "folderPath" not in txt and "/g/p" not in txt and ex["recipes"]["A.B/Make"]["ok"] == 1)
    rc = {"A.B/Make": {"status": "tool-ok"}, "Z/Q": {"status": "unverified"}}
    check("maintainer apply raises to proven", R.apply(rc, ex) == 1 and rc["A.B/Make"]["status"] == "proven" and rc["Z/Q"]["status"] == "unverified")
    check("report prints failures", "FAILED x1" in R.report(m))
    check("missing ledger is silent", R.evidence_from_ledger(os.path.join(d, "no.jsonl")) == {})
    pr = R.progress(ledger=led, recipes_path=os.path.join(d, "none.json"))
    check("progress is empty without a recipes file", pr == {})
    rp = os.path.join(d, "r.json")
    json.dump(recipes, open(rp, "w"))
    pr = R.progress(ledger=led, recipes_path=rp)
    check("progress counts statuses", pr.get("total") == len(recipes) and pr["proven"] + pr["tool_ok"] + pr["unverified"] == pr["total"])
    hp = os.path.join(d, "h.json")
    pr = R.progress(ledger=led, recipes_path=rp, history=hp)
    check("progress has areas and a weekly history line", pr["areas"] and sum(a["total"] for a in pr["areas"]) == pr["total"] and len(pr["history"]) == 1)
    pr = R.progress(ledger=led, recipes_path=rp, history=hp)
    check("history keeps one line per week", len(pr["history"]) == 1)
print("ALL PASS" if not fails else "%d FAIL" % len(fails))
sys.exit(1 if fails else 0)
