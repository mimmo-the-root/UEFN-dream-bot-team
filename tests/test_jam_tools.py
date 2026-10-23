import json, os, subprocess, sys, tempfile, shutil
H = os.path.join(os.path.dirname(__file__), "..", "project-template", "Claude", "hooks")
sys.path.insert(0, H)
import concept_card as cc, devlog, jam_check

# concept card: Epic's 7 criteria (70 points) + feasibility and scope (30 points)
ALL5 = dict(ambition=5, theme=5, fun=5, gameplay=5, visuals=5, level=5, audio=5, feasibility=5, scope=5)
ALL3 = {k: 3 for k in ALL5}
ALL2 = {k: 2 for k in ALL5}
assert cc.score(ALL5) == (100, "build it")
assert cc.score(ALL3) == (60, "build it only with a smaller scope")
assert cc.score(ALL2)[1] == "pick another idea"
assert cc.score(dict(ALL5, feasibility=1))[1] == "build it only with a smaller scope"
assert cc.score(dict(ALL5, theme=1))[1] == "pick another idea", "an idea that ignores the theme is not allowed"
no_theme = {k: v for k, v in ALL5.items() if k != "theme"}
assert cc.score(no_theme) == (100, "build it"), "without the theme the judging group is scaled over six criteria"
assert "not scored yet" in cc.card("T", "p", no_theme)
for bad in (dict(ALL5, fun=6), {"fun": 3}, dict(ALL5, hook=3)):
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
