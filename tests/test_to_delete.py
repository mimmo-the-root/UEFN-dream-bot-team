"""to_delete.py clean: only a parked folder (exact name) inside _to_delete is ever removed; names are never joined into a path (CodeQL py/path-injection)."""
import os, sys, tempfile, shutil
H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project-template", "Claude", "hooks")
sys.path.insert(0, H)
import to_delete as T
fails = []
def check(n, c):
    print(("PASS " if c else "FAIL ") + n)
    if not c: fails.append(n)
tmp = tempfile.mkdtemp()
try:
    proj = os.path.join(tmp, "proj"); r = os.path.join(proj, "_to_delete")
    for n in ("20261101-101010", "20261102-101010"):
        os.makedirs(os.path.join(r, n)); open(os.path.join(r, n, "f.txt"), "w").write("x")
    outside = os.path.join(tmp, "important"); os.makedirs(outside); open(os.path.join(outside, "keep.txt"), "w").write("x")
    check("list sees the two parked folders", T.listing(proj)["total"] == 2)
    for bad in ("../important", "..", "../../", "20261101-101010\n", "20261101-101010/..", "/etc", "", None, "20261101-101010x"):
        res = T.clean(proj, bad)
        check("a bad name is refused or does nothing: %r" % (bad,), not res.get("deleted") and os.path.isdir(outside) and len(os.listdir(r)) == 2)
    res = T.clean(proj, "20261101-101010")
    check("an exact parked name is deleted, the other stays", res == {"ok": True, "deleted": ["20261101-101010"]} and os.listdir(r) == ["20261102-101010"])
    if hasattr(os, "symlink"):
        try:
            os.symlink(outside, os.path.join(r, "20261103-101010"))
            res = T.clean(proj, "--all")
            check("a link out of _to_delete is not followed", os.path.exists(os.path.join(outside, "keep.txt")))
        except OSError:
            check("symlinks not available here: skipped", True)
    res = T.clean(proj, "--all")
    check("--all deletes the parked folders and nothing else", os.path.isdir(outside) and not [n for n in os.listdir(r) if os.path.isdir(os.path.join(r, n)) and not os.path.islink(os.path.join(r, n))])
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print("%d failed" % len(fails))
sys.exit(1 if fails else 0)
