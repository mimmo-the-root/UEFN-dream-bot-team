"""learn_gate.py: an already learned map learns once at the end of a release, not after every change."""
import os, sys, tempfile
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(root, "project-template", "Claude", "hooks"))
import learn_gate as g
p = tempfile.mkdtemp(); os.makedirs(os.path.join(p, "Claude", "docs"))
def roadmap(rows):
    open(os.path.join(p, "Claude", "docs", "ROADMAP.md"), "w", encoding="utf-8").write(
        "## Tasks\n\n| ID | Feature | Status | Acceptance criteria | Priority | Release |\n|---|---|---|---|---|---|\n" +
        "".join("| %s | f | %s | a | P1 | %s |\n" % r for r in rows))
os.environ.pop("UEFN_KIT_LEARN", None)
roadmap([("T-001", "Done", "P0-R1"), ("T-002", "In progress", "P0-R2"), ("T-003", "To do", "P0-R2")])
assert g.due(p, first_pass=True)[0], "the first learning always runs"
assert g.closed_releases(p) == ["P0-R1"]
assert not g.due(p)[0], "releases closed before the rule are not learned again"
assert not g.due(p)[0], "changes inside an open release wait"
roadmap([("T-001", "Done", "P0-R1"), ("T-002", "Done", "P0-R2"), ("T-003", "Done", "P0-R2"), ("T-004", "To do", "Later")])
d, why = g.due(p); assert d and "P0-R2" in why, why
assert g.due(p)[0], "stays due until the learning is finished"
g.mark_learned(p); assert not g.due(p)[0], "once per release"
os.environ["UEFN_KIT_LEARN"] = "every-change"; assert g.due(p)[0]; os.environ.pop("UEFN_KIT_LEARN")
open(os.path.join(p, "Claude", "LAB-PROJECT.txt"), "w").write("auto-recover: no\nlearn: every-change\n"); assert g.due(p)[0]
print("ok learn_gate")
