"""'Could not look' is never reported as a pass: release gate, Score and kit-doctor say NOT ASSESSED, and the rule file exists."""
import os, sys, tempfile
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
H = os.path.join(ROOT, "project-template", "Claude", "hooks")
sys.path.insert(0, H)
import release_gate as rg
bad = []
rules = open(os.path.join(ROOT, "project-template", "Claude", "reference", "CHECK-RULES.md"), encoding="utf-8").read()
for w in ("NOT ASSESSED", "newer than the work", "never assert", "skipped step"):
    if w.lower() not in rules.lower():
        bad.append("CHECK-RULES.md lacks: " + w)
d = tempfile.mkdtemp()
gate = "## 1. x\n- [x] a\n## 2. Compliance\n- Scan: pending (`/audit` runs it)\n## 4. y\n- Memory used: 50%\n"
na = rg.unassessed(gate, d)
if not any("scan" in x.lower() for x in na) or not any("AUDIT.md" in x for x in na) or not any("PLAYTEST.md" in x for x in na):
    bad.append("the gate does not list what it could not look at: %s" % na)
if rg.check(gate)[0]:
    bad.append("the fixture should have no blocking line")
ok_gate = gate.replace("pending (`/audit` runs it)", "0 blocks, 2 warnings")
open(os.path.join(d, "AUDIT.md"), "w").write("# audit\n")
open(os.path.join(d, "PLAYTEST.md"), "w").write("# p\n- [x] a | observed: fine\n")
if rg.unassessed(ok_gate, d):
    bad.append("a gate with scan, audit and an observed playtest must have nothing unassessed: %s" % rg.unassessed(ok_gate, d))
open(os.path.join(d, "PLAYTEST.md"), "w").write("# p\n- [ ] a | observed:\n")
if not rg.unassessed(ok_gate, d):
    bad.append("an unticked playtest row must be listed")
for f, w in (("score.py", "NOT ASSESSED"), ("kit_doctor.py", "NOT ASSESSED")):
    if w not in open(os.path.join(H, f), encoding="utf-8").read():
        bad.append(f + " does not use NOT ASSESSED")
for a in ("release-gate", "qa-regression"):
    if "CHECK-RULES" not in open(os.path.join(ROOT, "user-level-agents", a + ".md"), encoding="utf-8").read():
        bad.append(a + " agent does not point to CHECK-RULES.md")
print(("PASS " if not bad else "FAIL ") + "NOT ASSESSED is a verdict of its own" + ("" if not bad else ": " + "; ".join(bad[:5])))
sys.exit(1 if bad else 0)
