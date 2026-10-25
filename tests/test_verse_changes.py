import os, sys, tempfile, shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "project-template", "Claude", "hooks"))
import verse_changes as v

ok = "# A.verse\n# Summary: does x\n# Last modified: 2026-10-23 - v3\n\nusing { /Fortnite.com/Devices }\n"
assert v.check_header(ok) == []
assert v.check_header(ok.replace("\n# Summary: does x", "")) == ["no '# Summary:' line"]
assert any("Last modified" in p for p in v.check_header("# A.verse\n# Summary: s\nusing {}\n"))
assert any("history" in p for p in v.check_header(ok.replace("\n\nusing", "\n# v2 2026-10-01: old\n\nusing")))
assert v.check_header(ok.replace(" - v3", " — v3")) == [], "em dash form accepted"

d = tempfile.mkdtemp()
try:
    p = os.path.join(d, "Claude", "logs", "verse-changes.jsonl")
    assert v.record("Content/A.verse", "added respawn", "spec 12", path=p)
    assert v.record("A.verse", "fixed timer", result="errors", path=p)
    rows = v.read(p)
    assert len(rows) == 2 and rows[0]["file"] == "A.verse" and rows[1]["result"] == "errors"
    assert v.record("x", "y", path=os.path.join(d, "f.txt", "z", "q")) in (True, False)  # never raises
    rec = v.recurring([{"file": "A.verse", "result": "errors", "summary": "a"}, {"file": "A.verse", "result": "reverted", "summary": "b"}, {"file": "B.verse", "result": "errors"}, {"file": "C.verse", "result": "ok"}])
    assert rec == [("A.verse", 2, "b")], rec
    print("verse_changes tests OK")
finally:
    shutil.rmtree(d, ignore_errors=True)

# the log goes to the project's own Claude/logs even when started from a deeper folder (v1.109.1)
import tempfile as _tf, shutil as _sh
_d = _tf.mkdtemp()
try:
    os.makedirs(os.path.join(_d, "Claude", "hooks")); open(os.path.join(_d, "Claude", "hooks", "kit_sync.py"), "w").close()
    _deep = os.path.join(_d, "Claude", "docs"); os.makedirs(_deep)
    assert os.path.normcase(v.project_root(_deep)) == os.path.normcase(_d), v.project_root(_deep)
    print("PASS project_root walks up to the folder that holds Claude/hooks")
finally:
    _sh.rmtree(_d, ignore_errors=True)
