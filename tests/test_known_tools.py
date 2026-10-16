"""build_known_tools.py and the 'lab:' column of mcp_map.py --find (offline, temp files only)."""
import json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tool"))
sys.path.insert(0, os.path.join(ROOT, "project-template", "Claude", "hooks"))
import build_known_tools as B
import mcp_map as M

fails = 0
def ok(c, m):
    global fails
    print(("PASS " if c else "FAIL ") + m)
    fails += 0 if c else 1

d = tempfile.mkdtemp()
led = os.path.join(d, "l.jsonl")
open(led, "w").write("\n".join(json.dumps(x) for x in [
    {"toolset": "A.B", "tool": "Make", "r": "ok"}, {"toolset": "A.B", "tool": "Make", "r": "rejected"},
    {"toolset": "A.B", "tool": "DeleteIt", "r": "refused"}, {"toolset": "A.B", "tool": "NoAnswer", "r": "no_answer"},
    {"toolset": "A.B", "tool": "Rej", "r": "rejected"}]))
cov = {"A.B/Make": {"s": "ok"}, "A.B/DeleteIt": {"s": "refused", "why": "outside lab"}, "A.B/NoAnswer": {"s": "x", "why": ["slow"]},
       "A.B/Rej": {"s": "rejected", "why": "bad path"}, "A.B/Never": {"s": "u"}, "A.B/Recipe": {"s": "u"}}
json.dump(cov, open(os.path.join(d, "c.json"), "w")); json.dump({"A.B/Recipe#1": {}}, open(os.path.join(d, "r.json"), "w"))
t = B.build(led, os.path.join(d, "c.json"), os.path.join(d, "r.json"))
ok(t["A.B/Make"]["s"] == "ok", "ok wins over a later rejection")
ok(t["A.B/DeleteIt"]["s"] == "refused" and t["A.B/DeleteIt"].get("c") == 1 and t["A.B/DeleteIt"]["why"] == "outside lab", "refused + ask-first flag + reason")
ok(t["A.B/NoAnswer"]["s"] == "no_answer" and t["A.B/Rej"]["s"] == "rejected", "no_answer and rejected")
ok(t["A.B/Never"]["s"] == "never" and t["A.B/Recipe"]["s"] == "recipe", "never tried and recipe-only")
ok(M.lab_text(None) == "" and M.lab_text({"s": "never"}) == " | lab: not tried", "lab_text for unknown and untried tools")
ok(M.lab_text(t["A.B/DeleteIt"]) == " | lab: refused (outside lab) | ask the owner first", "lab_text with reason and flag")
shipped = json.load(open(os.path.join(ROOT, "project-template", "Claude", "hooks", "mcp-known-tools.json")))
ok(shipped["count"] == len(shipped["tools"]) > 300 and os.path.getsize(os.path.join(ROOT, "project-template", "Claude", "hooks", "mcp-known-tools.json")) < 120000, "shipped file is consistent and small")
print("all ok" if not fails else "%d failed" % fails)
sys.exit(1 if fails else 0)
