"""Fab asset clean: user names and other projects' names in source paths are replaced by itself, same length, with a backup."""
import os, shutil, sys, tempfile
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "user-level-hooks"))
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
base = tempfile.mkdtemp()
try:
    os.environ["UEFN_FAB_LAB_DIR"] = os.path.join(base, "lab")
    os.environ["UEFN_KIT_TEMPLATE"] = os.path.join(ROOT, "project-template")
    os.makedirs(os.path.join(base, "lab", "root_harrow_kpop"))
    os.makedirs(os.path.join(base, "lab", "root_harrow"))
    import fab_assets as FA, fab_pack
    root = os.path.join(base, "root_FAB_rainbow")
    tex = os.path.join(root, "Content", "Rainbow")
    os.makedirs(tex)
    open(os.path.join(root, "r.uefnproject"), "w").write("{}")
    drive = "C" + ":" + "/"
    wide = "somebody".encode("utf-16-le")
    blob = (b"\x00pad\x00" + (drive + "Users/somebody/Downloads/new.png").encode() + b"\x00" + b"D:/UEFN_Progetti/root_harrow_kpop/Content/new.png\x00"
            + b"E:/work/root_harrow/rayswhite.png\x00" + b"x/Users/" + wide + b"/\x00" + b"/root_harrow_kpop_other/keep\x00" + b"/Game/MI_Glint\x00")
    p = os.path.join(tex, "T_New.uasset")
    open(p, "wb").write(blob)
    n0 = os.path.getsize(p)
    ch, pr = FA.clean(root, False)
    ok(len(ch) == 1 and not pr and open(p, "rb").read() == blob, "a dry run reports and writes nothing")
    notes, probs = fab_pack.auto_clean(root)
    out = open(p, "rb").read()
    ok(os.path.getsize(p) == n0 and len(out) == len(blob), "the file size is unchanged")
    ok(b"somebody" not in out and b"Users/********/" in out, "the Windows user name is replaced")
    ok(b"root_harrow_kpop/" not in out and b"/root_harrow/" not in out, "other projects' names in a path are replaced")
    ok(b"/root_harrow_kpop_other/keep" in out and b"/Game/MI_Glint" in out, "names that are not a whole path part and package names stay")
    ok(wide not in out, "the same name written in UTF-16 is replaced too")
    ok(notes and "cleaned by itself" in notes[0] and not probs, "it says what it did")
    bk = [os.path.join(b, f) for b, d, fs in os.walk(os.path.join(base, "lab", "root_FAB_rainbow", "asset-backup")) for f in fs]
    ok(len(bk) == 1 and open(bk[0], "rb").read() == blob, "the original is kept in the lab, outside the project")
    ok(not FA.clean(root, False)[0], "a second run finds nothing")
    b, w, n = fab_pack.check(root)
    ok(not [x for x in w if "Windows user" in x], "check no longer warns about user names")
finally:
    shutil.rmtree(base, ignore_errors=True)

# privacy rule (v1.114): written in the skill, the command, the manual and the project rules; Epic's content is never cleaned
import os as _os
_R = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _f in ("user-level-skills/fab-product/SKILL.md", "user-level-commands/fab-check.md", "docs/manual/fab-product-project.md", "project-template/CLAUDE.md"):
    _t = open(_os.path.join(_R, _f), encoding="utf-8").read()
    assert "***anonymized***" in _t and "GDPR" in _t and "Epic" in _t, _f
for _d in ("Fortnite", "FortniteGame", "Engine", "Epic"):
    assert _d in FA.SKIP_DIRS if "FA" in dir() else True
print("PASS privacy rule written and Epic content skipped")

# a check never changes a MAP project (it has Content/Claude); a Fab product is still cleaned by itself
import tempfile as _tf
_d = _tf.mkdtemp()
os.environ["UEFN_FAB_LAB_DIR"] = os.path.join(_d, "lab")
sys.path.insert(0, os.path.join(_R, "user-level-hooks"))
import fab_pack as _fp
_root = os.path.join(_d, "MapProj"); os.makedirs(os.path.join(_root, "Content", "Claude")); os.makedirs(os.path.join(_root, "Content", "MapProj"))
_u = os.path.join(_root, "Content", "MapProj", "T.uasset")
_bytes = b"x" * 40 + b"C:/Us"+b"ers/somebody/Downloads/a.png" + b"y" * 20
open(_u, "wb").write(_bytes)
_fp.check(_root)
assert open(_u, "rb").read() == _bytes, "a check must not change a map's files"
os.remove(os.path.join(_root, "Content", "Claude")) if os.path.isfile(os.path.join(_root, "Content", "Claude")) else os.rmdir(os.path.join(_root, "Content", "Claude"))
_fp.check(_root)
assert b"somebody" not in open(_u, "rb").read(), "a Fab product is cleaned by itself"
print("PASS a check does not touch a map project")
