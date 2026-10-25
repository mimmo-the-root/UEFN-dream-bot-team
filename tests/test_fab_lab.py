"""Fab lab: lessons of a Fab product are recorded in the profile, never in the project."""
import json, os, shutil, subprocess, sys, tempfile
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "user-level-hooks"))
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
base = tempfile.mkdtemp()
try:
    os.environ["UEFN_FAB_LAB_DIR"] = os.path.join(base, "lab")
    os.environ["UEFN_KIT_TEMPLATE"] = os.path.join(ROOT, "project-template")
    import kit_install as ki, fab_lab as fl
    ki.REGISTRY = os.path.join(base, "kit-projects.json")

    def project(name, kind=None):
        r = os.path.join(base, name)
        os.makedirs(os.path.join(r, "Content"))
        open(os.path.join(r, name + ".uefnproject"), "w").write("{}")
        if kind:
            ki.set_kind(r, kind)
        return r

    def payload(r, tool, fail=False):
        p = {"cwd": os.path.join(r, "Content"), "session_id": "s1",
             "tool_input": {"toolset_name": "A.Materials", "tool_name": tool, "arguments": {"path": "/g/M_Barrier"}}}
        if fail:
            p.update(hook_event_name="PostToolUseFailure", error="Timeout while saving")
        else:
            p["tool_response"] = "{}"
        return p

    fab = project("Barrier", "fab")
    before = sorted(os.listdir(fab))
    ok(fl.record(payload(fab, "CreateMaterial")) is not None, "a Fab product call is recorded")
    ok(fl.record(payload(fab, "GetMaterial")) is not None and fl.record(payload(fab, "SetParameter", fail=True)) is not None, "reads and failures are recorded too")
    lg = fl.ledger_path(fab)
    ok(lg.startswith(base) and os.path.isfile(lg) and not lg.startswith(fab), "the ledger lives outside the project")
    ok(sorted(os.listdir(fab)) == before and not os.path.exists(os.path.join(fab, "Claude")), "nothing was written in the project")
    rows = [json.loads(x) for x in open(lg)]
    ok([r["r"] for r in rows] == ["ok", "ok", "rejected"] and rows[0]["sid"] == "s1", "rows have the normal ledger shape")
    ok(fl.record({"cwd": fab, "tool_input": {"command": "ls"}}) is None, "calls that are not UEFN MCP are ignored")
    a = fl.record({"cwd": fab, "hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_input": {"subagent_type": "materials-expert", "description": "audit materials"}})
    b = fl.record({"cwd": fab, "hook_event_name": "SubagentStop", "agent_type": "materials-expert"})
    ag = [json.loads(x) for x in open(os.path.join(fl.lab_dir(fab), "Claude", "logs", "agent-console.jsonl"))]
    ok(a and b and [x["event"] for x in ag] == ["start", "stop"] and ag[0]["agent"] == "materials-expert" and "ts" in ag[0], "subagent start and stop are logged for the console")
    ok(sorted(os.listdir(fab)) == before, "still nothing in the project")
    big = payload(fab, "RunScript")
    big["tool_input"]["arguments"] = {"script": "x" * 2500}
    fl.record(big)
    last = json.loads(open(lg).read().strip().split("\n")[-1])
    ok(len(json.loads(last["args"])["script"]) == 2500, "scripts are kept whole in the lab ledger (the map ledger cuts them at 60 characters)")
    mp = project("Island", "map")
    ok(fl.record(payload(mp, "CreateMaterial")) is None, "a map keeps its own hooks: not recorded here")
    un = project("Unknown")
    ok(fl.record(payload(un, "CreateMaterial")) is None, "an unregistered project is not recorded")
    s = fl.status(fab)
    ok(s["calls"] == 4 and s["failed"] == 1, "status counts calls and failures")
    p = fl.card(fab, "Barrier material")
    t = open(p, encoding="utf-8").read()
    ok(os.path.isfile(p) and not p.startswith(fab) and "CreateMaterial x1" in t and "SetParameter" in t and "TODO" in t, "closing card lists what changed and what failed")
    ok("GetMaterial" not in t.split("## What failed")[0], "reads are not listed as changes")
    p2 = fl.card(fab, "Barrier material")
    ok(p2 != p and os.path.isfile(p), "a second card does not overwrite the first")
    ok(os.path.isfile(os.path.join(fl.lab_dir(fab), "Claude", "KIT-VERSION")), "lab has a KIT-VERSION so the console shows it")
    out = subprocess.run([sys.executable, os.path.join(ROOT, "user-level-hooks", "fab_lab.py"), "hook"], input=json.dumps(payload(fab, "CreateMaterial")),
                         text=True, capture_output=True, env=dict(os.environ, HOME=base, USERPROFILE=base))
    ok(out.returncode == 0, "the hook always exits 0")
    # the console reads the lab, not the project folder
    code = ("import sys,os;sys.argv=['x','0'];sys.path.insert(0,r'%s');import importlib.util as u;"
            "s=u.spec_from_file_location('srv',r'%s');m=u.module_from_spec(s);s.loader.exec_module(m);print(m.PROJECT_DIR);print(m.LOGS_DIR)"
            % (os.path.join(ROOT, "project-template", "Claude", "hooks"), os.path.join(ROOT, "project-template", "Claude", "hooks", "agent-console-server.py")))
    lab = fl.lab_dir(fab)
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=dict(os.environ, UEFN_FAB_LAB=lab))
    lines = r.stdout.split("\n")
    ok(r.returncode == 0 and lines[0] == lab and lines[1] == os.path.join(lab, "Claude", "logs"), "console server uses the lab folder when UEFN_FAB_LAB is set")
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env={k: v for k, v in os.environ.items() if k != "UEFN_FAB_LAB"})
    ok(r.returncode == 0 and r.stdout.split("\n")[0].endswith("UEFNDreamTeamBot") or "project-template" in r.stdout.split("\n")[0], "without it the server keeps using the project")
finally:
    shutil.rmtree(base, ignore_errors=True)
