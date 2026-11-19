import json, os, shutil, sys, tempfile
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(root, "tools"))
import lab_permissions as lp

d = tempfile.mkdtemp()
try:
    proj = os.path.join(d, "p"); os.makedirs(os.path.join(proj, ".claude"))
    sp = os.path.join(proj, ".claude", "settings.json")
    orig = {"hooks": {"Stop": [{"x": 1}]}, "permissions": {"allow": ["Bash(ls:*)"], "deny": ["Bash(sudo:*)"]}, "model": "m"}
    def write(o): open(sp, "w").write(json.dumps(o, indent=2) + "\n")
    def read(): return json.load(open(sp))
    write(orig); raw = open(sp).read()
    # no marker = no change
    open(os.path.join(proj, "LAB-PROJECT.txt"), "w").write("name: x\n")
    assert lp.apply(proj)[0] is False and open(sp).read() == raw
    assert lp.check_missing(proj) == ""
    # marker = block added, other keys kept, nothing allowed
    open(os.path.join(proj, "LAB-PROJECT.txt"), "a").write("lab-permissions: prudent\n")
    assert lp.check_missing(proj)
    assert lp.apply(proj)[0] is True
    s = read()
    assert s["hooks"] == orig["hooks"] and s["model"] == "m" and s["permissions"]["allow"] == ["Bash(ls:*)"]
    assert "Bash(sudo:*)" in s["permissions"]["deny"] and "Bash(git push:*)" in s["permissions"]["deny"]
    assert lp.check_missing(proj) == ""
    # second run = no change
    after = open(sp).read()
    assert lp.apply(proj)[0] is False and open(sp).read() == after
    # --remove restores
    assert lp.main([proj, "--remove"]) == 0
    assert read() == orig
    # doctor warns when missing
    sys.path.insert(0, os.path.join(root, "project-template", "Claude", "hooks"))
    os.environ["UEFN_KIT_TEMPLATE"] = os.path.join(root, "project-template")
    os.environ["UEFN_HOME"] = os.path.join(d, "home"); os.makedirs(os.environ["UEFN_HOME"])
    import kit_doctor
    assert any("lab-permissions" in t or "LAB-PROJECT" in t for _s, t in kit_doctor.check(proj))
    lp.apply(proj)
    assert not any("LAB-PROJECT" in t for _s, t in kit_doctor.check(proj))
    print("ok")
finally:
    shutil.rmtree(d, ignore_errors=True)
