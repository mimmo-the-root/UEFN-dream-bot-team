"""Delivery document: auto part rebuilt from ROADMAP/BUGS, free part kept."""
import os, shutil, sys, tempfile
H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project-template", "Claude", "hooks")
sys.path.insert(0, H)
import delivery
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
d = tempfile.mkdtemp()
try:
    docs = os.path.join(d, "Claude", "docs"); os.makedirs(docs)
    hdr = "| ID | Feature | Status | Acceptance criteria | Priority | Release |\n|---|---|---|---|---|---|\n"
    open(os.path.join(docs, "ROADMAP.md"), "w").write("# Roadmap\n\n## Tasks\n\n" + hdr + "| T-001 | Core loop | Done | x | P1 | P0-R1 |\n| T-002 | Music | To do | x | P2 | P0-R2 |\n")
    open(os.path.join(docs, "BUGS.md"), "w").write("# Bugs\n\n| Title | Where | Severity | Probable cause | Status |\n|---|---|---|---|---|\n| B-001: crash at start | A.verse | major | x | Open |\n")
    t = delivery.build(d)
    ok("Tasks finished: 1 of 2" in t and "T-001: Core loop" in t and "B-001: crash at start" in t, "state, finished tasks and open bugs are listed")
    p = delivery.write(d)
    s = open(p).read()
    ok("## How to play (fill in)" in s, "free part is created once")
    open(p, "w").write(s.replace("Controls and goal:", "Controls and goal: WASD"))
    open(os.path.join(docs, "BUGS.md"), "a").write("| B-002: other | B.verse | minor | x | Open |\n")
    delivery.write(d)
    s2 = open(p).read()
    ok("WASD" in s2 and "B-002: other" in s2 and s2.count(delivery.START) == 1, "rewrite keeps hand text and refreshes the auto part")
finally:
    shutil.rmtree(d, ignore_errors=True)
