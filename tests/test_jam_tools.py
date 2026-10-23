import json, os, subprocess, sys, tempfile, shutil
H = os.path.join(os.path.dirname(__file__), "..", "project-template", "Claude", "hooks")
sys.path.insert(0, H)
import concept_card as cc, devlog, jam_check

# concept card
assert cc.score(dict(feasibility=5, scope=5, hook=5, retention=5, originality=5, showability=5)) == (100, "build it")
t, v = cc.score(dict(feasibility=3, scope=3, hook=3, retention=3, originality=3, showability=3)); assert (t, v) == (60, "build it only with a smaller scope")
assert cc.score(dict(feasibility=1, scope=5, hook=5, retention=5, originality=5, showability=5))[1] == "build it only with a smaller scope"
assert cc.score(dict(feasibility=2, scope=2, hook=2, retention=2, originality=2, showability=2))[1] == "pick another idea"
for bad in (dict(feasibility=6, scope=1, hook=1, retention=1, originality=1, showability=1), dict(feasibility=1)):
    try: cc.score(bad); raise SystemExit("should fail")
    except ValueError: pass

d = tempfile.mkdtemp()
try:
    proj = os.path.join(d, "MyIsland"); c = os.path.join(proj, "Content")
    os.makedirs(os.path.join(c, "Claude", "logs")); os.makedirs(os.path.join(c, "Claude", "docs"))
    lg = os.path.join(c, "Claude", "logs")
    open(os.path.join(lg, "verse-changes.jsonl"), "w").write(json.dumps({"ts": "2026-10-23T10:00:00Z", "file": "A.verse", "summary": "added respawn", "reason": "spec", "result": "ok"}) + "\n")
    open(os.path.join(lg, "verse-errors.jsonl"), "w").write(json.dumps({"ts": "2026-10-23T11:00:00Z", "errors": 1, "sigs": ["H123"], "excerpt": "x"}) + "\n")
    p = devlog.write(c); t1 = open(p).read()
    assert "How AI was used" in t1 and "added respawn" in t1 and "H123" in t1
    open(p, "w").write(t1.replace("What the human decided:", "What the human decided: the theme"))
    devlog.write(c); t2 = open(p).read()
    assert "the theme" in t2 and t2.count("<!-- auto:start -->") == 1, "text outside the markers is kept, one auto block"
    # jam check
    open(os.path.join(c, "Good.verse"), "w").write("# Good.verse\n# Summary: ok\n# Last modified: 2026-10-23 - v1\nx:=1\n")
    open(os.path.join(c, "Bad.verse"), "w").write("# Bad.verse\n# Summary: ok\n# Last modified: 2026-10-23 - v2\n# v1 2026-10-01: old\nx:=1\n")
    os.makedirs(os.path.join(c, "L" * 150)); open(os.path.join(c, "L" * 150, "Mesh.uasset"), "w").close()
    open(os.path.join(c, "bad name.uasset"), "w").close()
    b, w = jam_check.check(c)
    assert any("Bad.verse" in x and "history" in x for x in b) and not any("Good.verse" in x for x in b)
    assert any("characters" in x and "path is" in x for x in b)
    assert any("bad name" in x for x in w) and any("concept-card" in x for x in w)
    r = subprocess.run([sys.executable, os.path.join(H, "jam_check.py"), c], capture_output=True, text=True)
    assert r.returncode == 1 and "Only you can confirm" in r.stdout
    print("jam tools tests OK")
finally:
    shutil.rmtree(d, ignore_errors=True)
