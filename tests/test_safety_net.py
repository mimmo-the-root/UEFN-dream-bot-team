import os, subprocess, sys, shutil, tempfile, time
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
S = os.path.join(root, "project-template", "Claude", "hooks", "safety_net.py")
d = tempfile.mkdtemp()
def run(*a):
    r = subprocess.run([sys.executable, S, *a], cwd=d, capture_output=True, text=True); assert r.returncode == 0, r.stdout + r.stderr; return r.stdout
def w(rel, txt):
    p = os.path.join(d, *rel.split("/")); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(txt)
try:
    w("game/a.verse", "A1"); w("game/b.verse", "B1"); w("Claude/docs/STATUS.md", "S1"); w("Claude/logs/x.verse", "ignored")
    assert "created" in run("snapshot", "--why", "before refactor")
    assert "No changes" in run("snapshot")
    time.sleep(1.1)
    w("game/a.verse", "A2"); w("game/c.verse", "C1"); os.remove(os.path.join(d, "game", "b.verse"))
    out = run("changes")
    assert "modified" in out and "game/a.verse" in out and "added" in out and "game/c.verse" in out and "deleted" in out and "game/b.verse" in out, out
    assert "1 modified, 1 added, 1 deleted" in run("changes", "--brief")
    pid = run("list").split()[0]
    assert "Would restore 2" in run("restore", pid) and open(os.path.join(d, "game", "a.verse")).read() == "A2"
    assert "Restored 2" in run("restore", pid, "--apply")
    assert open(os.path.join(d, "game", "a.verse")).read() == "A1" and open(os.path.join(d, "game", "b.verse")).read() == "B1"
    assert os.path.exists(os.path.join(d, "game", "c.verse")), "added file must be left in place"
    assert len(run("list").strip().splitlines()) == 2, "restore must create a point of the pre-restore state"
    for b, _, fs in os.walk(os.path.join(d, "Claude", "logs", "restore-points")):
        assert not [f for f in fs if f.endswith(".verse")], "restore point must not contain compilable .verse"
    # kit_sync makes a restore point at session start
    d2 = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(d2, "Claude")); open(os.path.join(d2, "m.verse"), "w").write("x")
        sys.path.insert(0, os.path.join(root, "project-template", "Claude", "hooks"))
        os.environ["UEFN_KIT_TEMPLATE"] = os.path.join(d2, "none")
        import kit_sync, safety_net
        kit_sync.run(d2)
        assert len(safety_net.points(d2)) == 1, "no session-start restore point"
    finally:
        shutil.rmtree(d2, ignore_errors=True)
    print("safety net tests OK")
finally:
    shutil.rmtree(d, ignore_errors=True)
