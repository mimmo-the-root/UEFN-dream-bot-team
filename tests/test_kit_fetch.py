import os, subprocess, sys, shutil, tempfile, zipfile
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
d = tempfile.mkdtemp()
def run(env, *a, cwd=None):
    e = dict(os.environ, **env)
    return subprocess.run([sys.executable, os.path.join(root, "project-template", "Claude", "hooks", "kit_fetch.py"), *a],
                          capture_output=True, text=True, env=e, cwd=cwd)
try:
    home, proj, z = os.path.join(d, "home"), os.path.join(d, "proj"), os.path.join(d, "rel.zip")
    os.makedirs(os.path.join(home, "skills", "genre", "x", "local")); os.makedirs(os.path.join(home, "agents"))
    open(os.path.join(home, "skills", "genre", "x", "local", "private.json"), "w").write("keep")
    open(os.path.join(home, "agents", "coder.md"), "w").write("old agent")
    shutil.copytree(os.path.join(root, "project-template"), proj)
    open(os.path.join(proj, "Claude", "KIT-VERSION"), "w").write("0.1.0\n")
    with zipfile.ZipFile(z, "w") as zf:
        for part in ("project-template", "user-level-agents", "user-level-skills"):
            for b, ds, fs in os.walk(os.path.join(root, part)):
                ds[:] = [x for x in ds if x != "__pycache__"]
                for f in fs:
                    p = os.path.join(b, f); zf.write(p, "owner-repo-abc123/" + os.path.relpath(p, root).replace(os.sep, "/"))
        zf.writestr("owner-repo-abc123/user-level-skills/genre/roguelike/local/evil.json", "x")
    env = {"UEFN_HOME": home, "UEFN_KIT_TEMPLATE": ""}
    env.pop("UEFN_KIT_TEMPLATE")
    r = run({"UEFN_HOME": home, "UEFN_KIT_TEMPLATE": os.path.join(home, "kit-template")}, "--zip", z, cwd=proj)
    assert r.returncode == 0 and "profile file(s) updated" in r.stdout, r.stdout + r.stderr
    ver = open(os.path.join(root, "project-template", "Claude", "KIT-VERSION")).read().strip()
    assert open(os.path.join(home, "kit-template", "Claude", "KIT-VERSION")).read().strip() == ver
    assert open(os.path.join(proj, "Claude", "KIT-VERSION")).read().strip() == ver, "project not synced"
    assert open(os.path.join(home, "agents", "coder.md")).read() != "old agent"
    bk = os.path.join(home, "kit-backup"); assert any(f == "coder.md" for _, _, fs in os.walk(bk) for f in fs), "no backup of replaced agent"
    assert open(os.path.join(home, "skills", "genre", "x", "local", "private.json")).read() == "keep"
    assert not os.path.exists(os.path.join(home, "skills", "genre", "roguelike", "local")), "local/ from zip must be skipped"
    r2 = run({"UEFN_HOME": home, "UEFN_KIT_TEMPLATE": os.path.join(home, "kit-template")}, "--zip", z, cwd=proj)
    assert "already up to date" in r2.stdout, r2.stdout
    # unsafe zip and non-kit zip are refused, nothing changes
    bad = os.path.join(d, "bad.zip")
    with zipfile.ZipFile(bad, "w") as zf:
        zf.writestr("o/project-template/Claude/KIT-VERSION", "9.9.9"); zf.writestr("o/project-template/../../evil.txt", "x")
    r3 = run({"UEFN_HOME": home, "UEFN_KIT_TEMPLATE": os.path.join(home, "kit-template")}, "--zip", bad, cwd=proj)
    assert r3.returncode == 1 and "unsafe path" in r3.stdout and not os.path.exists(os.path.join(d, "evil.txt"))
    nokit = os.path.join(d, "nokit.zip")
    with zipfile.ZipFile(nokit, "w") as zf: zf.writestr("o/readme.md", "x")
    assert run({"UEFN_HOME": home}, "--zip", nokit, cwd=proj).returncode == 1
    print("kit fetch tests OK")
finally:
    shutil.rmtree(d, ignore_errors=True)
