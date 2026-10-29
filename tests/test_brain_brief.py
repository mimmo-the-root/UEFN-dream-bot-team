"""brain_brief.py: the second brain hooks (session start brief, check after a wiki edit). Off and silent while the vault path is the placeholder."""
import json, os, shutil, subprocess, sys, tempfile
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
B = os.path.join(root, "project-template", "Claude", "hooks", "brain_brief.py")
SK = os.path.join(root, "user-level-skills", "second-brain-query")
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
home, vault = tempfile.mkdtemp(), tempfile.mkdtemp()
try:
    shutil.copytree(SK, os.path.join(home, "skills", "second-brain-query"))
    def run(mode, stdin="", **env):
        e = dict(os.environ, UEFN_HOME=home); e.pop("SECOND_BRAIN", None); e.update(env)
        return subprocess.run([sys.executable, B, mode], input=stdin, capture_output=True, text=True, env=e)
    def w(rel, txt):
        p = os.path.join(vault, *rel.split("/")); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w", encoding="utf-8").write(txt)
    open(os.path.join(home, "CLAUDE.md"), "w").write("**Second brain path**: `<SECOND_BRAIN_PATH>`\n")
    r = run("start"); ok(r.returncode == 0 and r.stdout == "", "the placeholder keeps the second brain off and silent")
    open(os.path.join(home, "CLAUDE.md"), "w").write("**Second brain path**: `%s`\n" % vault)
    w("raw/memex.md", "The essential feature is the association of ideas.\n")
    w("wiki/hot.md", "# Hot\n- working on the round timer\n")
    r = run("start")
    ok(r.returncode == 0 and "Second brain is on" in r.stdout and "round timer" in r.stdout and "1 pending" in r.stdout, "start prints the read order, hot.md and the pending ingest")
    w("wiki/mechanics/a.md", '---\ncreated: 2026-01-01\n---\n> "association of ideas" - raw/memex.md\n')
    page = os.path.join(vault, "wiki", "mechanics", "a.md")
    r = run("after-edit", json.dumps({"tool_input": {"file_path": page}})); ok(r.returncode == 0, "a page with a true quote and no broken link passes")
    w("wiki/mechanics/a.md", '---\ncreated: 2026-01-01\n---\n> "Bush invented hypertext in 1941" - raw/memex.md\nsee [[missing-page]]\n')
    r = run("after-edit", json.dumps({"tool_input": {"file_path": page}}))
    ok(r.returncode == 2 and "QUOTE NOT IN SOURCE" in r.stderr and "missing-page" in r.stderr, "a false quote and a broken link come back to Claude (exit 2)")
    r = run("after-edit", json.dumps({"tool_input": {"file_path": os.path.join(home, "other.md")}})); ok(r.returncode == 0, "an edit outside the vault wiki is ignored")
    r = run("after-edit", "not json"); ok(r.returncode == 0, "bad input never blocks")
    r = run("start", SECOND_BRAIN=os.path.join(home, "nowhere")); ok(r.returncode == 0 and r.stdout == "", "a path that is not a folder is treated as off")
finally:
    shutil.rmtree(home, ignore_errors=True); shutil.rmtree(vault, ignore_errors=True)
print("brain brief tests OK")
