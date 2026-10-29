"""kit-doctor: the five needs (instructions, state, verification, scope, hand-over), critical or recommended."""
import os, shutil, sys, tempfile, time
H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project-template", "Claude", "hooks")
sys.path.insert(0, H)
import kit_doctor
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
hdr = "| ID | Feature | Status | Acceptance criteria | Priority | Release |\n|---|---|---|---|---|---|\n"
d = tempfile.mkdtemp()
try:
    ok(kit_doctor.five_needs(d) == [], "a project without Claude/docs is skipped")
    docs = os.path.join(d, "Claude", "docs"); os.makedirs(docs)
    open(os.path.join(docs, "ROADMAP.md"), "w").write("# R\n\n## Tasks\n\n" + hdr + "| T-001 | A | Done | works | P1 | P0-R1 |\n| T-002 | B | To do |  | P1 | P0-R1 |\n")
    r = dict((t.split(":")[0], s) for s, t in kit_doctor.five_needs(d))
    ok(r["Instructions"] == "PROBLEM", "no CLAUDE.md with the kit block is critical")
    ok(r["State"] == "PROBLEM", "no status page is critical")
    ok(r["Verification"] == "PROBLEM", "a Done task with no playtest, audit or delivery list is critical")
    ok(r["Scope"] == "NOTE", "a task without a check is only recommended")
    open(os.path.join(d, "CLAUDE.md"), "w").write("<!-- KIT:BEGIN x -->\nrules\n<!-- KIT:END x -->\n")
    open(os.path.join(docs, "STATUS.md"), "w").write("status")
    open(os.path.join(docs, "PLAYTEST.md"), "w").write("checks")
    r = dict((t.split(":")[0], s) for s, t in kit_doctor.five_needs(d))
    ok(r["Instructions"] == r["State"] == r["Verification"] == "OK", "with rules, a fresh status and a playtest list the critical needs pass")
    old = time.time() - 20 * 86400; os.utime(os.path.join(docs, "STATUS.md"), (old, old))
    ok(dict((t.split(":")[0], s) for s, t in kit_doctor.five_needs(d))["State"] == "PROBLEM", "a status page older than 14 days is critical")
    run = os.path.join(d, "Claude", "relay", "running"); os.makedirs(run)
    open(os.path.join(run, "007-x.md"), "w").write("id: 007"); os.utime(os.path.join(run, "007-x.md"), (old, old))
    ok(dict((t.split(":")[0], s) for s, t in kit_doctor.five_needs(d))["Hand-over"] == "PROBLEM", "a command left in running/ for over an hour is critical")
finally:
    shutil.rmtree(d, ignore_errors=True)
print("five needs tests OK")
