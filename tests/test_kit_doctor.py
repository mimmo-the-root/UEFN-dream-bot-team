import os, sys, shutil, tempfile
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
tplsrc = os.path.join(root, "project-template")
d = tempfile.mkdtemp()
try:
    tpl, home, proj = (os.path.join(d, x) for x in ("tpl", "home", "proj"))
    shutil.copytree(tplsrc, tpl)
    os.makedirs(home)
    shutil.copytree(tplsrc, proj)
    os.environ["UEFN_KIT_TEMPLATE"] = tpl
    os.environ["UEFN_HOME"] = home
    sys.path.insert(0, os.path.join(tplsrc, "Claude", "hooks"))
    import kit_doctor
    def status(res, key):
        return [s for s, t in res if key in t]
    # healthy
    res = kit_doctor.check(proj)
    assert not [1 for s, _ in res if s == "PROBLEM"], res
    # stale project version
    open(os.path.join(tpl, "Claude", "KIT-VERSION"), "w").write("99.0.0\n")
    assert status(kit_doctor.check(proj), "99.0.0") == ["PROBLEM"]
    res = kit_doctor.check(proj, fix=True)
    assert status(res, "updated from kit") == ["FIXED"], res
    assert open(os.path.join(proj, "Claude", "KIT-VERSION")).read().strip() == "99.0.0"
    # stray .verse backup
    lg = os.path.join(proj, "Claude", "logs", "kit-backup"); os.makedirs(lg, exist_ok=True)
    open(os.path.join(lg, "X.verse"), "w").write("x")
    assert status(kit_doctor.check(proj), ".verse") == ["PROBLEM"]
    assert status(kit_doctor.check(proj, fix=True), ".verse") == ["FIXED"]
    assert os.path.isfile(os.path.join(lg, "X.verse.bak")) and not os.path.exists(os.path.join(lg, "X.verse"))
    # broken settings
    sp = os.path.join(proj, ".claude", "settings.json"); good = open(sp).read()
    open(sp, "w").write("{ nope")
    assert status(kit_doctor.check(proj), "not valid JSON") == ["PROBLEM"]
    open(sp, "w").write(good)
    # second brain path
    open(os.path.join(home, "CLAUDE.md"), "w").write("**Second brain path**: `%s`\n" % os.path.join(d, "nowhere"))
    assert status(kit_doctor.check(proj), "not a valid vault") == ["PROBLEM"]
    open(os.path.join(home, "CLAUDE.md"), "w").write("**Second brain path**: `<SECOND_BRAIN_PATH>`\n")
    assert not status(kit_doctor.check(proj), "not a valid vault")
    # .mcp.json outside .gitignore
    os.makedirs(os.path.join(proj, ".git")); open(os.path.join(proj, ".mcp.json"), "w").write("{}")
    assert status(kit_doctor.check(proj), ".mcp.json may hold") == ["PROBLEM"]
    assert status(kit_doctor.check(proj, fix=True), ".mcp.json added") == ["FIXED"]
    assert status(kit_doctor.check(proj), "ignored by git") == ["OK"]
    print("kit doctor tests OK")
finally:
    shutil.rmtree(d, ignore_errors=True)
