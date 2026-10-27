"""env_check.py (v1.114): environment readout and playtest checklist from the Chicken Roundup fixtures. Read only."""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = os.path.join(ROOT, "project-template", "Claude", "hooks")
sys.path.insert(0, H)
import env_check as ec

def rd(*p):
    return open(os.path.join(ROOT, *p), encoding="utf-8").read()

d = os.path.join(tempfile.mkdtemp(), "Claude", "docs")
os.makedirs(d)
open(os.path.join(d, "GAME-SPEC.md"), "w", encoding="utf-8").write(rd("tests", "fixtures", "game-spec-chicken-roundup.md"))
open(os.path.join(d, "PLAN.md"), "w", encoding="utf-8").write(rd("tests", "fixtures", "plan-chicken.md"))
e = ec.environment(d)
assert len(e["assets"]) == 4 and [a[1] for a in e["to_get"]] == ["Grass and trees allowed in a playable island", "Delivery sound"] and e["approved"]
assert len(e["manual"]) == 1 and "Details panel" in e["manual"][0][1]
t = ec.playtest(d)
assert "## S1 - Round up the chickens (P1)" in t and "SC-003" in t and "- [ ] Given a tamed chicken" in t and "Observed:" in t
base = os.path.dirname(os.path.dirname(d))
p = subprocess.run([sys.executable, os.path.join(H, "env_check.py"), base], capture_output=True, text=True)
assert p.returncode == 0 and "2 to import or create" in p.stdout and "Only the owner" in p.stdout, p.stdout
p = subprocess.run([sys.executable, os.path.join(H, "env_check.py"), base, "--playtest"], capture_output=True, text=True)
assert p.returncode == 0 and "Playtest checklist" in p.stdout
empty = tempfile.mkdtemp()
p = subprocess.run([sys.executable, os.path.join(H, "env_check.py"), empty], capture_output=True, text=True)
assert p.returncode == 1
print("ok")

# pilot demo (v1.114): shipped files pass the kit's own checks; copy never overwrites; load only in an empty project
import demo_pilot as dp, spec_check, plan_check
dd = os.path.join(ROOT, "project-template", "Claude", "reference", "demo-chicken-roundup")
assert set(dp.files()) == {"GAME-SPEC.md", "CONSTITUTION.md", "PLAN.md", "ROADMAP.md", "PLAYTEST.md", "README.md"}
blk, _, _ = spec_check.check(open(os.path.join(dd, "GAME-SPEC.md"), encoding="utf-8").read())
assert not blk, blk
tmp = tempfile.mkdtemp()
os.makedirs(os.path.join(tmp, "Claude", "docs"))
assert dp.main(["copy", tmp]) == 0 and os.path.isfile(os.path.join(tmp, "Claude", "docs", "demo-chicken-roundup", "PLAN.md"))
assert dp.main(["load", tmp]) == 0 and os.path.isfile(os.path.join(tmp, "Claude", "docs", "GAME-SPEC.md"))
assert dp.main(["load", tmp]) == 1
assert "demo_pilot.py" in rd("user-level-commands", "demo.md")
print("ok demo")
