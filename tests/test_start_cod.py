"""T-084: cod.cmd has the --safe start and passes the mode to session-settings; docs/START-COD.md lists the 4 start commands."""
import os, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
bad = 0


def ok(c, m):
    global bad
    print(("PASS " if c else "FAIL ") + m)
    bad += 0 if c else 1


cmd = open(os.path.join(ROOT, "user-level-hooks", "cod.cmd"), encoding="utf-8").read()
ok('"%~1"=="--safe"' in cmd and "set MODE=safe" in cmd, "cod.cmd has --safe and sets MODE=safe")
ok("session-settings %MODE%" in cmd, "cod.cmd passes the mode to session-settings")
for f in ("--auto", "--plan", "--free"):
    ok('"%~1"=="' + f + '"' in cmd, "cod.cmd keeps " + f)
doc = open(os.path.join(ROOT, "docs", "START-COD.md"), encoding="utf-8").read()
for c in ("cod.cmd", "cod.cmd --free", "cod.cmd --plan", "cod.cmd --safe"):
    ok("`" + c + "`" in doc, "START-COD.md lists " + c)
sys.exit(1 if bad else 0)
