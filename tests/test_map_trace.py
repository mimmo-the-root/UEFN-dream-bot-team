"""map_trace: traces of other projects in a map are warnings recorded once in BUGS.md; Fab products are skipped."""
import os, shutil, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "user-level-hooks"))
import map_trace as MT
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
base = tempfile.mkdtemp()
try:
    root = os.path.join(base, "Map")
    mine = "11111111-2222-3333-4444-555555555555"
    os.makedirs(os.path.join(root, "Content", "Prod"))
    os.makedirs(os.path.join(root, "Claude", "docs"))
    open(os.path.join(root, "Map.uefnproject"), "w").write("{}")
    open(os.path.join(root, mine + ".uplugin"), "w").write("{}")
    shutil.copy(os.path.join(HERE, "..", "project-template", "Claude", "docs-template", "BUGS.md"), os.path.join(root, "Claude", "docs", "BUGS.md"))
    f, n = MT.scan(root)
    ok(not f, "a clean map: nothing found")
    ok(MT.record(root, ["x"]) == "added", "a finding is recorded as a bug row")
    t = open(os.path.join(root, "Claude", "docs", "BUGS.md"), encoding="utf-8").read()
    ok("B-002: " + MT.TITLE in t and "| Title | Where |" in t.split("## Newly reported")[1], "the row has the next id and sits under Newly reported")
    ok(MT.record(root, ["x"]) == "exists", "it is recorded once")
    ok(MT.main([root]) == 0, "the command runs")
finally:
    shutil.rmtree(base, ignore_errors=True)
print("OK")
