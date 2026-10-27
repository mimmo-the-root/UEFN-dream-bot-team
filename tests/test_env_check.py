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

# v1.114: players and Island settings, release gate, audit ledger, phase times
import plan_check as pk, release_gate as rg, audit_log as al, run_log as rl
spec = rd("tests", "fixtures", "game-spec-chicken-roundup.md")
b, w, i = spec_check.check(spec.replace("- Players: 4\n", ""))
assert any(x.startswith("Players:") for x in b)
b, w, i = spec_check.check(spec)
assert not b and any("4 players" in x for x in i)
plan = rd("tests", "fixtures", "plan-chicken.md")
def mkdocs(p):
    dd = os.path.join(tempfile.mkdtemp(), "Claude", "docs")
    os.makedirs(dd)
    for n, t in (("GAME-SPEC.md", spec), ("CONSTITUTION.md", rd("tests", "fixtures", "constitution-chicken.md")), ("PLAN.md", p), ("ROADMAP.md", rd("tests", "fixtures", "roadmap-chicken.md"))):
        open(os.path.join(dd, n), "w", encoding="utf-8").write(t)
    return dd
assert not [f for f in pk.check(mkdocs(plan)) if f[0] in ("CRITICAL", "HIGH")]
no_isl = plan.split("## Island settings")[0] + "## Build order" + plan.split("## Build order", 1)[1]
assert any("Island settings" in f[1] and f[0] == "HIGH" for f in pk.check(mkdocs(no_isl)))
low = plan.replace("| Max players | 4 |", "| Max players | 2 |")
assert any("lower than the players" in f[1] for f in pk.check(mkdocs(low)))
assert "Island Settings: Max players = 4" in " ".join(ec.environment(mkdocs(plan))["owner"])
assert "Play with 4 players" in ec.playtest(mkdocs(plan))
# release gate: nothing is ticked by Claude; memory has to be written
gd = mkdocs(plan)
assert rg.main(["init", os.path.dirname(os.path.dirname(gd))]) == 0
gt = open(os.path.join(gd, "DELIVERY-GATE.md"), encoding="utf-8").read()
blk, wr = rg.check(gt)
assert len(blk) >= 8 and any("Memory used" in x for x in blk) and "Island Settings: Max players = 4" in gt
ticked = gt.replace("- [ ]", "- [x]").replace("<NN>%", "90%")
blk, wr = rg.check(ticked)
assert not blk and wr and "90%" in wr[0]
assert rg.check(ticked.replace("90%", "100%"))[0]
assert rg.main(["init", os.path.dirname(os.path.dirname(gd))]) == 0 and open(os.path.join(gd, "DELIVERY-GATE.md"), encoding="utf-8").read() == gt
# audit ledger: limits of the self-healing
it = al.add([], "old Verse header", "minor", "a.verse")
for _ in range(2):
    it = al.fix(it, 1, False)
assert it[0]["cls"] == "minor"
it = al.fix(it, 1, False)
assert it[0]["cls"] == "medium" and it[0]["state"] == "for the owner"
it = al.add(it, "score wrong with 4 players", "major")
try:
    al.fix(it, 2, True)
    raise SystemExit("a major finding must not be fixed alone")
except ValueError:
    pass
assert al.status(it)[0] == {"minor": 0, "medium": 1, "major": 1}
many = []
for k in range(11):
    many = al.add(many, "m%d" % k, "minor")
for k in range(1, 11):
    many = al.fix(many, k, True)
try:
    al.fix(many, 11, True)
    raise SystemExit("the 11th automatic fix must be refused")
except ValueError:
    pass
# phase times
bt = tempfile.mkdtemp()
os.makedirs(os.path.join(bt, "Claude"))
rl.add("start", "1 spec", now=1000, base=bt)
rl.add("stop", "1 spec", note="ok", tokens=500, now=1000 + 600, base=bt)
rl.add("start", "2 plan", now=2000, base=bt)
r = rl.report(bt)
assert "| 1 spec | 10.0 | 500 | ok |" in r and "| 2 plan | open" in r
for name, words in (("audit", ("audit_log.py", "codebase-auditor", "Self-healing")), ("consegna", ("release_gate.py", "never ticks", "Memory")),):
    c = rd("user-level-commands", name + ".md")
    assert c.startswith("---") and "description:" in c, name
    for w_ in words:
        assert w_.lower() in c.lower(), (name, w_)
print("ok v114")
