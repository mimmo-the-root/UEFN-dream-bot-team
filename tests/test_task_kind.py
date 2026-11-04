import os, sys
root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(root, "project-template", "Claude", "hooks"))
import docs_migrate as dm

OLD = """## Tasks

| ID | Feature | Status | Acceptance criteria | Priority | Release |
|---|---|---|---|---|---|
| T-001 | Spawn pads | Fatto | works | P1 | P0-R1 |
| T-002 | Fix crash on respawn (B-033) | Da fare | no crash | P1 | P1-R1 |
| T-003 | Audit 2026-11-04 finding #7: null check in score.verse | Da fare | fixed | P2 | P1-R1 |
| T-004 | Performance: reduce tick cost (PERF #2) | Da fare | under 2 ms | P2 | P1-R1 |
| T-005 | Audit minor findings (12 items) | Da fare | all fixed | P3 | P1-R1 |
"""

def rows(t):
    out = []
    for l in t.split("\n"):
        if l.startswith("| T-"):
            out.append(dm.split(l))
    return out

new, notes = dm.migrate_roadmap(OLD)
head = dm.split([l for l in new.split("\n") if l.startswith("| ID")][0])
assert head == ["ID", "Feature", "Status", "Acceptance criteria", "Priority", "Release", "Kind", "Source"], head
r = {x[0]: x for x in rows(new)}
assert r["T-001"][6:] == ["feature", ""], r["T-001"]
assert r["T-002"][6:] == ["bug", "B-033"], r["T-002"]
assert r["T-003"][6:] == ["audit", "AUDIT #7"], r["T-003"]
assert r["T-004"][6:] == ["perf", "PERF #2"], r["T-004"]
assert r["T-005"][6] == "audit", r["T-005"]
# idempotent, and a hand-set Kind is never overwritten
again, n2 = dm.migrate_roadmap(new)
assert again == new and not n2
edited = new.replace("| feature |  |", "| bug | B-001 |")
again2, _ = dm.migrate_roadmap(edited)
assert "| bug | B-001 |" in again2
# a table grouped by blank lines (header only on top) is converted in full
grp = OLD.replace("| T-003", "\n<!-- next block -->\n| T-003")
g, _ = dm.migrate_roadmap(grp)
gr = {x[0]: x for x in rows(g)}
assert len(gr["T-004"]) == 8 and gr["T-004"][6] == "perf", gr["T-004"]
print("task kind tests OK")
