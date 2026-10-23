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
    check("verified is shown as tool-ok", R.merge({"A/k": {"args": {}, "status": "verified"}}, {})["A/k"]["status"] == "tool-ok")
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
td = R.todo({"A/x": {"status": "proven"}, "A/y": {"status": "tool-ok"}, "B/z": {"status": "unverified"}})
check("todo skips proven recipes", [k for _, k, _ in td] == ["A/y", "B/z"])
check("todo can be limited to one area", R.todo({"A/y": {"status": "tool-ok"}}, area="nope") == [])
with tempfile.TemporaryDirectory() as d2:
    led2 = os.path.join(d2, "l.jsonl")
    open(led2, "w").write(json.dumps({"toolset": "A.B", "tool": "Other", "r": "ok", "src": "replay", "args": json.dumps({"x": 9})}) + "\n" + json.dumps({"toolset": "A.B", "tool": "Make", "r": "ok", "src": "battery", "args": json.dumps({"name": "N"})}) + "\n")
    m2 = R.merge(recipes, R.evidence_from_ledger(led2))
    check("a replay row makes a recipe proven, a battery row does not", m2["A.B/Other"]["status"] == "proven" and m2["A.B/Make#v2"]["status"] != "proven")
nm = R.merge({"recipe/multi step": {"args": {}, "status": "unverified"}, "Plain note (X/y)": {"args": {}}, "MatTools/set_parent#v": {"args": {"p": 1}, "status": "verified"}},
             {"editor.mat.MatTools/set_parent": {R.form({"p": 2}): [1, 0, ""]}})
check("multi-step notes are notes, not recipes", nm["recipe/multi step"]["status"] == "note" and nm["Plain note (X/y)"]["status"] == "note")
check("a short toolset name matches the full class name in the ledger", nm["MatTools/set_parent#v"]["status"] == "proven")
check("todo and progress leave notes out", R.todo(nm) == [])
tc = R.tool_coverage({"A/x": {"status": "proven"}, "A/y": {"status": "tool-ok"}, "Short/z#v": {"status": "tool-ok"}, "recipe/n": {"status": "note"}},
                     ["A/x", "A/y", "A/w", "ns.Short/z"])
check("tool coverage: tools with a recipe and with a proven one, short names match, notes cover nothing", tc == (3, 1))
with tempfile.TemporaryDirectory() as d3:
    l3 = os.path.join(d3, "l.jsonl")
    open(l3, "w").write(json.dumps({"toolset": "ns", "tool": "Q", "r": "ok", "args": '{"a": 1}'}) + "\n")
    g = R.gap({"ns/P": {"status": "tool-ok"}}, {"ns/P": {"s": "ok", "a": "x"}, "ns/Q": {"s": "ok", "a": "x"}, "ns/R": {"s": "rejected"}}, l3)
    check("gap lists answered tools with no recipe and their last good call", g == [("x", "ns/Q", '{"a": 1}')])
av = R.merge({"A/x": {"args": {}, "status": "avoid"}}, {"A/x": {R.form({}): [3, 0, ""]}})
check("an `avoid` recipe stays avoid (a known trap) and is not replayed", av["A/x"]["status"] == "avoid" and R.todo(av) == [])
# ---- stale recipes after a UEFN change ----
import recipes_status as _R
_rec = {"A.B/Make": {"args": {}, "status": "proven"}, "A.B/Keep": {"args": {}, "status": "proven"}, "A.B/Gone#note": {}, "A.B/Old": {"args": {}, "status": "tool-ok"}}
_rows = [{"date": "2026-10-01", "uefn": "41.00", "state": "changed", "removed": ["A.B/Old"], "changed": ["A.B/Make"]},
         {"date": "2026-10-10", "uefn": "41.10", "state": "unchanged"}]
_s = _R.stale(_rec, _rows)
assert sorted((k, w) for k, w, _, _ in _s) == [("A.B/Make", "tool changed"), ("A.B/Old", "tool removed")], _s
assert _R.stale(_rec, _rows, since="2026-10-01") == [], "a retest stamp hides older changes"
print("PASS stale recipes: changed and removed tools are listed, retest stamp hides old changes")
print("ALL PASS" if not fails else "%d FAIL" % len(fails))
sys.exit(1 if fails else 0)
