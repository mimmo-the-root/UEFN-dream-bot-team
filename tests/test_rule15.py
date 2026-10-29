"""install-rule15.py adds the second-brain block to a user CLAUDE.md once, refreshes it, and never touches the rest."""
import os, subprocess, sys, tempfile, shutil
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
S, SEC = os.path.join(root, "tool", "install-rule15.py"), os.path.join(root, "user-level-memory", "section-15-second-brain-session.md")
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
d = tempfile.mkdtemp()
try:
    f = os.path.join(d, "CLAUDE.md"); open(f, "w", newline="").write("# Mine\r\n\r\n**Second brain path**: `C:\\vault`\r\n")
    run = lambda: subprocess.run([sys.executable, S, SEC, f], capture_output=True, text=True).stdout
    ok("added" in run(), "the block is added to an existing profile file")
    t = open(f, newline="").read()
    ok(t.startswith("# Mine\r\n\r\n**Second brain path**: `C:\\vault`") and t.count("KIT:BEGIN second-brain-session") == 1 and "\r\n" in t and "\n\n" not in t.replace("\r\n", ""), "the user's own lines and line endings stay")
    ok("refreshed" in run() and open(f, newline="").read() == t, "running it again changes nothing")
    tpl = open(os.path.join(root, "user-level-memory", "CLAUDE.md"), encoding="utf-8").read()
    ok("rule 15" in tpl and tpl.count("KIT:BEGIN second-brain-session") == 1, "the profile template carries the block and rule 11 points to it")
finally:
    shutil.rmtree(d, ignore_errors=True)
print("rule 15 tests OK")
