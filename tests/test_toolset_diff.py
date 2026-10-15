"""MCP map: first map, unchanged, added/removed/changed with what the new tools do, shared storage, read/write guess, kit usage."""
import os, sys, json, tempfile, subprocess
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
script = os.path.join(root, "project-template", "Claude", "hooks", "toolset_diff.py")
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))

def run(d, data, *args):
    r = subprocess.run([sys.executable, script, "--dir", d] + list(args), input=data if isinstance(data, str) else json.dumps(data), capture_output=True, text=True)
    return r.returncode, json.loads(r.stdout.strip().splitlines()[-1])

d = tempfile.mkdtemp()
a = {"tools": {"UMG/GetWidgets": "Reads the widget tree. More detail here.", "Assets/find_assets": "Finds assets by name.", "Assets/save_assets": "Saves the listed assets to disk."}}
c, r = run(d, a, "--uefn-version", "42.40")
ok(c == 0 and r["state"] == "first_snapshot" and r["count"] == 3 and r["toolsets"] == 2, "first call saves a map")
ok(r["kit_uses"] == 3 and r["kit_uses_pct"] == 100.0, "usage by the kit is counted by tool name")
latest = json.load(open(os.path.join(d, "latest.json")))
ok(latest["uefn_version"] == "42.40" and latest["tools"]["UMG/GetWidgets"]["a"] == "read" and latest["tools"]["Assets/save_assets"]["a"] == "write", "read and write are guessed from the name")
ok(latest["tools"]["UMG/GetWidgets"]["d"] == "Reads the widget tree.", "only the first sentence of the description is kept")
mp = open(os.path.join(d, "MAP.md"), encoding="utf-8").read()
ok("3 tools" in mp and "[kit]" in mp and "## UMG" in mp, "MAP.md is written, grouped by toolset, kit tools marked")
c, r = run(d, a); ok(c == 0 and r["state"] == "unchanged", "same tools -> unchanged")
b = {"tools": {"UMG/GetWidgets": "Reads the widget tree and bindings.", "UMG/RenderPreview": "Renders a picture of a widget.", "Assets/find_assets": "Finds assets by name."}}
c, r = run(d, b)
ok(c == 1 and r["state"] == "changed" and r["added"][0]["tool"] == "UMG/RenderPreview" and r["added"][0]["does"] == "Renders a picture of a widget." and r["removed"] == ["Assets/save_assets"] and r["changed"] == ["UMG/GetWidgets"], "new tools come with what they do; removed and changed are told apart")
ok(r["added"][0]["access"] == "?" , "an unknown verb is not guessed")
ok(os.listdir(os.path.join(d, "history")) and len(open(os.path.join(d, "changes.jsonl")).read().strip().splitlines()) == 2, "the old map is kept in history and every change is logged")
c, r = run(d, b); ok(r["state"] == "unchanged", "the changed map became the new baseline")
w = tempfile.mkdtemp()
run(w, {"toolsets": [{"name": "UMG", "tools": [{"name": "GetWidgets", "description": "Reads the widget tree. More detail here."}]}]})
c, r = run(w, {"tools": {"UMG/GetWidgets": "Reads the widget tree. More detail here."}})
ok(r["state"] == "unchanged", "toolsets shape and tools shape give the same names")
c, r = run(d, "not json"); ok(c == 2 and r["state"] == "bad_input", "bad input -> exit 2")
c, r = run(d, {"tools": {}}); ok(c == 2, "empty list is refused, never saved as a baseline")
q = tempfile.mkdtemp(); run(q, a, "--no-save"); ok(not os.path.exists(os.path.join(q, "latest.json")), "--no-save writes nothing")
r = subprocess.run([sys.executable, script, "--dir", tempfile.mkdtemp(), "--no-save"], input=json.dumps({"tools": {"diff": "a", "set/create": "b"}}), capture_output=True, text=True)
ok("1 tool names" in json.loads(r.stdout)["warning"], "names without a toolset prefix are warned about")
env = dict(os.environ, UEFN_KIT_MCP_DIR=os.path.join(tempfile.mkdtemp(), "shared"))
subprocess.run([sys.executable, script], input=json.dumps(a), capture_output=True, text=True, env=env)
ok(os.path.isfile(os.path.join(env["UEFN_KIT_MCP_DIR"], "latest.json")), "one shared map for all projects (UEFN_KIT_MCP_DIR / default profile folder)")
