"""UEFN MCP recipes: what your own work proved reaches the kit at the release, and the console says what is not in the kit yet."""
import json, os, subprocess, sys, tempfile
d = tempfile.mkdtemp(); os.environ["HOME"] = d; os.environ["USERPROFILE"] = d
os.environ["UEFN_FAB_LAB_DIR"] = os.path.join(d, "lab")
os.environ["UEFN_MCP_EVIDENCE"] = os.path.join(d, "mcp-evidence.json")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "project-template", "Claude", "hooks")); sys.path.insert(0, os.path.join(ROOT, "tool"))
import recipes_status as RS
import collect_mcp_evidence as CE
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))

rp = os.path.join(d, "recipes.json")
rec = {"T.Set/DoIt": {"args": {"name": "x"}, "status": "unverified"}, "T.Set/Done": {"args": {"name": "x"}, "status": "proven"}, "T.Set/Other": {"args": {"a": 1}, "status": "tool-ok"}}
open(rp, "w", encoding="utf-8", newline="").write(json.dumps(rec, indent=2, ensure_ascii=False))
proj = os.path.join(d, "MyFab"); os.makedirs(os.path.join(proj, "Claude", "logs"))
json.dump({proj: {"kind": "fab", "name": "MyFab"}}, open((os.makedirs(os.path.join(d, ".claude"), exist_ok=True) or os.path.join(d, ".claude", "kit-projects.json")), "w"))
led = os.path.join(proj, "Claude", "logs", "explore-ledger.jsonl")
open(led, "w").write(json.dumps({"toolset": "T.Set", "tool": "DoIt", "src": "work", "r": "ok", "args": json.dumps({"name": "abc"})}) + "\n")
RS.sync()
os.remove(led); import shutil; shutil.rmtree(proj)
ok(os.path.exists(os.environ["UEFN_MCP_EVIDENCE"]) and "abc" not in open(os.environ["UEFN_MCP_EVIDENCE"]).read(), "the profile store keeps only the call form, never the values")
pen0 = RS.pending(tools=["T.Set/DoIt"], recipes_path=rp, changes=[])
ok(pen0["proven_local"] == ["T.Set/DoIt"], "deleting the project and its ledger loses nothing")
os.makedirs(os.path.join(proj, "Claude", "logs"))
open(led, "w").write(json.dumps({"toolset": "T.Set", "tool": "DoIt", "src": "work", "r": "ok", "args": json.dumps({"name": "abc"})}) + "\n")
ok(RS.ledger_paths() == [led], "the ledgers of the registered projects are found")
pen = RS.pending(tools=["T.Set/DoIt", "T.Set/Brand"], recipes_path=rp, changes=[])
ok(pen["proven_local"] == ["T.Set/DoIt"], "a recipe proven by your work but not proven in the kit is listed as pending")
new = CE.collect(dry=True, recipes_path=rp)
ok(new == ["T.Set/DoIt"] and json.load(open(rp))["T.Set/DoIt"]["status"] == "unverified", "dry run changes nothing")
new = CE.collect(recipes_path=rp)
got = json.load(open(rp))
ok(got["T.Set/DoIt"]["status"] == "proven" and got["T.Set/Other"]["status"] == "tool-ok" and got["T.Set/Done"]["status"] == "proven", "the release marks it proven and leaves every other status alone")
ok(open(rp, encoding="utf-8").read() == json.dumps(got, indent=2, ensure_ascii=False), "the file keeps its layout (a release only changes the status lines)")
ok(CE.collect(recipes_path=rp) == [], "running it again changes nothing")
import skills_lib as SL
os.environ["UEFN_SKILLS_DIR"] = os.path.join(d, "skills")
rec2 = json.load(open(rp)); rec2["T.Set/DoIt"]["status"] = "unverified"
open(rp, "w", encoding="utf-8", newline="").write(json.dumps(rec2, indent=2, ensure_ascii=False))
SL.hold_set("mcp", "T.Set/DoIt", True)
ok(CE.collect(recipes_path=rp) == [], "a recipe kept private on the Skills page is not released")
SL.hold_set("mcp", "T.Set/DoIt", False)
ok(CE.collect(recipes_path=rp) == ["T.Set/DoIt"], "and goes out again once it is shareable")
import mcp_work_log, inspect
ok("note_ok" in inspect.getsource(mcp_work_log), "the work log hook feeds the profile store")
html = open(os.path.join(ROOT, "project-template", "Claude", "hooks", "agent-console-skills.html"), encoding="utf-8").read()
ok("Not in the kit yet" in html and "m.pending" in html, "the UEFN MCP tab shows what is not in the kit yet")
print("OK")
