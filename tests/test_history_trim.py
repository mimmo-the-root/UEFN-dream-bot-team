import os, sys, tempfile, shutil, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "project-template", "Claude", "hooks"))
import history_trim as h

def code_lines(t):
    return [l for l in t.splitlines() if not l.lstrip().startswith("#")]

d = tempfile.mkdtemp()
try:
    os.makedirs(os.path.join(d, "Claude", "docs"))
    hist = "\n".join("# FIX line %d of the old history of this thing" % i for i in range(12))
    v = "using { /Fortnite.com/Devices }\n" + hist + "\nmy_class := class:\n    X:int = 1\n" + "# pad\n" * 4000
    p = os.path.join(d, "a.verse"); open(p, "w").write(v)
    r1 = h.run(d, apply=True)
    new = open(p).read()
    assert r1 and code_lines(new) == [l for l in code_lines(v)], "code must be untouched"
    assert len(new) < len(v) and "history," in new
    for b, _, fs in os.walk(os.path.join(d, "Claude", "logs")):
        assert not [f for f in fs if f.endswith(".verse")], "backup must not be a .verse file"
    assert h.run(d, apply=True) == [], "idempotent"
    assert os.path.isdir(os.path.join(d, "Claude", "docs", "archive", "verse"))
    open(os.path.join(d, "Claude", "docs", ".no-history-trim"), "w").close()
    open(p, "w").write(v)
    assert h.run(d, apply=True) == [], "opt-out"
    print("history_trim tests OK")
finally:
    shutil.rmtree(d, ignore_errors=True)

# v1.108: header history is removed from ANY size of file, Summary + Last modified stay, code untouched, one log row
d = tempfile.mkdtemp()
try:
    hv = ("# B.verse\n# Summary: Spawns waves.\n# Last modified: 2026-10-23 - v7\n"
          "# v6 2026-10-01: fixed timer\n# v1-v5: initial build\nusing { /Fortnite.com/Devices }\nc := class:\n    X:int = 1\n")
    p2 = os.path.join(d, "b.verse"); open(p2, "w").write(hv)
    r = h.run(d, apply=True)
    n2 = open(p2).read()
    assert r and "header history" in r[0], r
    assert "Summary: Spawns waves." in n2 and "Last modified: 2026-10-23 - v7" in n2
    assert "v6 2026" not in n2 and "v1-v5" not in n2
    assert code_lines(n2) == code_lines(hv)
    assert h.run(d, apply=True) == [], "idempotent"
    lg = open(os.path.join(d, "Claude", "logs", "verse-changes.jsonl")).read()
    assert '"migrated"' in lg and "b.verse" in lg
    print("header history migration OK")
finally:
    shutil.rmtree(d, ignore_errors=True)
