"""skills_lib.second_brain_state(): what the Console badge shows (off, pages, raw sources waiting)."""
import os, shutil, sys, tempfile
H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project-template", "Claude", "hooks")
sys.path.insert(0, H)
import skills_lib
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
home, vault = tempfile.mkdtemp(), tempfile.mkdtemp()
try:
    os.environ["UEFN_HOME"] = home; os.environ.pop("SECOND_BRAIN", None)
    def w(rel, t):
        p = os.path.join(vault, *rel.split("/")); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w", encoding="utf-8").write(t)
    open(os.path.join(home, "CLAUDE.md"), "w").write("**Second brain path**: `<SECOND_BRAIN_PATH>`\n")
    ok(skills_lib.second_brain_state() == {"on": False, "pages": 0, "pending": 0}, "the placeholder means off")
    open(os.path.join(home, "CLAUDE.md"), "w").write("**Second brain path**: `%s`\n" % vault)
    ok(skills_lib.second_brain_state()["on"] is False, "a folder without wiki/ is off")
    w("wiki/index.md", "# i"); w("wiki/hot.md", "# h"); w("wiki/kit/wiki-index.md", "# k"); w("wiki/kit/a.md", "a"); w("wiki/mechanics/b.md", "b")
    w("raw/s1.md", "one"); w("raw/s2_COMPILED.md", "two")
    st = skills_lib.second_brain_state()
    ok(st["on"] and st["pages"] == 2 and st["pending"] == 2, "counts pages (not index, hot or log) and sources never ingested: %r" % st)
    import hashlib, json
    sha = lambda t: hashlib.sha256(t.encode()).hexdigest()[:16]
    os.makedirs(os.path.join(vault, ".brain")); json.dump({"raw/s1.md": {"sha": sha("one"), "pages": []}, "raw/s2.md": {"sha": sha("two"), "pages": []}}, open(os.path.join(vault, ".brain", "manifest.json"), "w"))
    ok(skills_lib.second_brain_state()["pending"] == 0, "ingested sources (a _COMPILED name is the same source) wait for nothing")
    w("raw/s1.md", "one, edited")
    ok(skills_lib.second_brain_state()["pending"] == 1, "a source edited after ingest waits again")
finally:
    shutil.rmtree(home, ignore_errors=True); shutil.rmtree(vault, ignore_errors=True)
print("brain state tests OK")
