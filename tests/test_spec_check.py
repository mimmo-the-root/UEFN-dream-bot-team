import datetime, os, re, subprocess, sys, tempfile
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
H = os.path.join(ROOT, "project-template", "Claude", "hooks")
sys.path.insert(0, H)
import spec_check as sc

tpl = open(os.path.join(ROOT, "project-template", "Claude", "docs-template", "GAME-SPEC.md"), encoding="utf-8").read()
ok = open(os.path.join(ROOT, "tests", "fixtures", "game-spec-chicken-roundup.md"), encoding="utf-8").read()
D1, D2 = datetime.date(2026, 11, 1), datetime.date(2026, 11, 12)

# the empty template is not ready: it blocks on every required part
b, w, i = sc.check(tpl)
assert len(b) >= 6, b
assert any("Loop" in x for x in b) and any("P1" in x or "Story" in x for x in b) and any("Technical risks" in x for x in b)

# a finished spec is ready, and the high risk is shown before approval
b, w, i = sc.check(ok, gate=True)
assert b == [], b
assert any("High risk" in x for x in i), i

# an old SPEC.md (deduced from code) is not a game spec
r = sc.check("# Project spec\n\n## Project structure\nx\n")
assert r[0] and "not a game spec" in r[0][0]

# gate: needs approval and a score of 60 (or the owner's force)
b, _, _ = sc.check(ok.replace("Approved: yes", "Approved: no"), gate=True)
assert any("Not approved" in x for x in b)
b, _, _ = sc.check(ok.replace("72/100", "50/100"), gate=True)
assert any("below 60" in x for x in b)
b, _, i = sc.check(ok.replace("72/100", "50/100").replace("Forced: no", "Forced: yes"), gate=True)
assert b == [] and any("forced" in x for x in i)
b, _, _ = sc.check(ok.replace("Score: 72/100", "Score: <NN>/100"), gate=True)
assert any("Score: not written" in x for x in b)
b, _, _ = sc.check(ok.replace("72/100", "50/100"))  # quality check without gate does not care about the score
assert b == []

# an open clarification blocks; an empty loop line blocks
b, _, _ = sc.check(ok.replace("- None.", "- [NEEDS CLARIFICATION: how long is a round?]"))
assert any("NEEDS CLARIFICATION" in x for x in b)
b, _, _ = sc.check(ok.replace("- Replay: ", "- Replay: <").replace("Replay: <", "Replay: <why>"))
assert any("Replay" in x for x in b)

# a story without a test, and a risk table without a level
b, _, _ = sc.check(ok.replace("- Independent test: start a round", "- Independent test: <start a round"))
assert any("independent test" in x for x in b)
b, _, _ = sc.check(re.sub(r"\| (high|medium) \|", "| ? |", ok))
assert any("Technical risks" in x for x in b)

# jam mode: the theme line is a warning before 11 November and blocks after
b, w, _ = sc.check(ok, jam=True, today=D1)
assert b == [] and any("Theme" in x for x in w)
b, _, _ = sc.check(ok, jam=True, today=D2)
assert any("Theme" in x for x in b)
b, _, _ = sc.check(ok.replace("theme enters the game:", "theme enters the game: the farm is a lost garden"), jam=True, today=D2)
assert b == []
b, _, _ = sc.check(ok.replace("- Mode: normal", "- Mode: jam"), today=D2)
assert any("Theme" in x for x in b), "Mode: jam in the file is enough"

# command line: finds the spec in Claude/docs, exit code follows the blocks, no spec = exit 1
d = tempfile.mkdtemp()
os.makedirs(os.path.join(d, "Claude", "docs"))
p = subprocess.run([sys.executable, os.path.join(H, "spec_check.py"), d], capture_output=True, text=True)
assert p.returncode == 1 and "run /spec" in p.stdout
open(os.path.join(d, "Claude", "docs", "GAME-SPEC.md"), "w", encoding="utf-8").write(ok)
p = subprocess.run([sys.executable, os.path.join(H, "spec_check.py"), d, "--gate"], capture_output=True, text=True)
assert p.returncode == 0 and "ready for planning" in p.stdout, p.stdout
open(os.path.join(d, "Claude", "docs", "GAME-SPEC.md"), "w", encoding="utf-8").write(tpl)
p = subprocess.run([sys.executable, os.path.join(H, "spec_check.py"), d], capture_output=True, text=True)
assert p.returncode == 1 and "BLOCK" in p.stdout

# the /spec command exists, with its front matter, and names the file and the checker
cmd = open(os.path.join(ROOT, "user-level-commands", "spec.md"), encoding="utf-8").read()
assert cmd.startswith("---") and "description:" in cmd and "GAME-SPEC.md" in cmd and "spec_check.py" in cmd and "concept_card.py" in cmd
print("ok")
