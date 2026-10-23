import json, os, subprocess, sys, tempfile, shutil

hooks = os.path.join(os.path.dirname(__file__), "..", "user-level-hooks")
home = tempfile.mkdtemp()
os.environ["HOME"] = home
os.environ["USERPROFILE"] = home
sys.path.insert(0, hooks)
import kit_install as ki

try:
    tpl = os.path.join(home, ".claude", "kit-template")
    for rel, txt in (("CLAUDE.md", "x"), ("Claude/hooks/kit_sync.py", "y"), ("Claude/logs/a.jsonl", "l"), ("Claude/KIT-VERSION.tmp", "t"), (".claude/settings.json", "{}")):
        p = os.path.join(tpl, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(txt)
    root = os.path.join(home, "MyMap"); content = os.path.join(root, "Content")
    os.makedirs(content); open(os.path.join(root, "MyMap.uefnproject"), "w").close()
    assert ki.find_uefn_root(content)[0] == root and ki.find_uefn_root(root)[1] == content
    assert ki.find_uefn_root(home) is None
    files = ki.plan(content)
    assert files == sorted([".claude/settings.json".replace("/", os.sep), "CLAUDE.md", os.path.join("Claude", "hooks", "kit_sync.py")]), files  # no logs, no .tmp
    open(os.path.join(content, "CLAUDE.md"), "w").write("mine")
    assert "CLAUDE.md" not in ki.plan(content), "existing file is never replaced"
    ki.apply(content)
    assert open(os.path.join(content, "CLAUDE.md")).read() == "mine"
    assert ki.kit_installed(content) and ki.plan(content) == [], "second run copies nothing"
    # global hook: a new map asks the question; a Fab product never gets the kit
    hook = os.path.join(hooks, "kit-sync-global.py")
    os.makedirs(os.path.join(home, ".claude", "hooks"), exist_ok=True)
    shutil.copy(os.path.join(hooks, "kit_install.py"), os.path.join(home, ".claude", "hooks"))
    def run_hook(cwd):
        env = dict(os.environ)
        return subprocess.run([sys.executable, hook], input=json.dumps({"cwd": cwd}), capture_output=True, text=True, env=env).stdout
    fab = os.path.join(home, "FabX"); os.makedirs(os.path.join(fab, "Content")); open(os.path.join(fab, "FabX.uefnproject"), "w").close()
    shutil.copy(hook, os.path.join(home, ".claude", "hooks"))
    hook = os.path.join(home, ".claude", "hooks", "kit-sync-global.py")
    os.makedirs(os.path.join(tpl, "Claude", "hooks"), exist_ok=True)
    out = run_hook(os.path.join(fab, "Content"))
    assert "map (island) or a Fab product" in out, out
    assert ki.main(["--kind", fab, "fab"]) == 0 and ki.get_kind(fab) == "fab"
    assert "FAB PRODUCT" in run_hook(os.path.join(fab, "Content"))
    assert ki.main([os.path.join(fab, "Content"), "--apply"]) == 3
    assert not os.path.exists(os.path.join(fab, "Content", "CLAUDE.md")), "project-template must never go into a Fab product"
    assert run_hook(content) == "", "a project that already has the kit stays silent"
    print("kit_install tests OK")
finally:
    shutil.rmtree(home, ignore_errors=True)
