import os, re, shutil, subprocess, sys, tempfile
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
H = os.path.join(ROOT, "project-template", "Claude", "hooks")
T = os.path.join(ROOT, "project-template", "Claude", "docs-template")
FX = os.path.join(ROOT, "tests", "fixtures")
sys.path.insert(0, H)
import plan_check as pc


def rd(*p):
    return open(os.path.join(*p), encoding="utf-8").read()


def make(spec=None, const=None, plan=None, road=None):
    d = tempfile.mkdtemp()
    docs = os.path.join(d, "Claude", "docs")
    os.makedirs(docs)
    for name, txt, fx in (("GAME-SPEC.md", spec, "game-spec-chicken-roundup.md"), ("CONSTITUTION.md", const, "constitution-chicken.md"),
                          ("PLAN.md", plan, "plan-chicken.md"), ("ROADMAP.md", road, "roadmap-chicken.md")):
        t = rd(FX, fx) if txt is None else txt
        if t:
            open(os.path.join(docs, name), "w", encoding="utf-8").write(t)
    return docs


def sev(F, s, word):
    return any(x[0] == s and word in x[1] for x in F)


# the complete example is coherent
assert pc.check(make()) == [], pc.check(make())

# the empty templates are not: the template plan and constitution are flagged, the spec gate too
F = pc.check(make(const=rd(T, "CONSTITUTION.md"), plan=rd(T, "PLAN.md")))
assert sev(F, "HIGH", "placeholders") and sev(F, "HIGH", "has no section")

# spec not approved: CRITICAL, planning is not allowed
F = pc.check(make(spec=rd(FX, "game-spec-chicken-roundup.md").replace("Approved: yes", "Approved: no")))
assert sev(F, "CRITICAL", "not ready for planning")
F = pc.check(make(spec=""), "all")
assert F[0][0] == "CRITICAL" and "run /spec" in F[0][1]

# constitution conflict is always CRITICAL, in the plan or in a task
F = pc.check(make(plan=rd(FX, "plan-chicken.md").replace("sounds for the delivery", "a leaderboard board")))
assert sev(F, "CRITICAL", "leaderboard")
F = pc.check(make(road=rd(FX, "roadmap-chicken.md").replace("Round timer and end of round", "Multiplayer round timer")))
assert sev(F, "CRITICAL", "multiplayer")
F = pc.check(make(plan=rd(FX, "plan-chicken.md").replace("leaderboard", "x")), "plan")  # nothing forbidden here
assert not sev(F, "CRITICAL", "forbidden")

# plan: a story without section, Pass 1 not starting from S1, a device table without status
F = pc.check(make(plan=re.sub(r"(?s)## S2 - .*?(?=## Risks)", "", rd(FX, "plan-chicken.md"))))
assert sev(F, "HIGH", "Story 2")
F = pc.check(make(plan=rd(FX, "plan-chicken.md").replace("S1 first: the farm", "the farm")))
assert sev(F, "HIGH", "Pass 1")
F = pc.check(make(plan=rd(FX, "plan-chicken.md").replace("| explore |", "| ? |").replace("| skill |", "| ? |").replace("| recipe |", "| ? |")))
assert sev(F, "MEDIUM", "devices table")

# tasks: a story with no task, no criterion, a missing dependency, a cycle, an unreduced high risk
road = rd(FX, "roadmap-chicken.md")
F = pc.check(make(road=road.replace("[S2]", "[S1]")))
assert sev(F, "HIGH", "Story 2")
F = pc.check(make(road=road.replace("The owner assigns the references, Claude checks them and the build is clean", "(short)")))
assert sev(F, "HIGH", "T-001 has no verifiable")
F = pc.check(make(road=road.replace("(after T-003)", "(after T-099)")))
assert sev(F, "HIGH", "T-099")
F = pc.check(make(road=road.replace("[S1] [R1] |", "[S1] [R1] (after T-004) |")))
assert sev(F, "HIGH", "cycle")
F = pc.check(make(road=road.replace(" [R1]", "")))
assert sev(F, "HIGH", "High risk R1")
F = pc.check(make(road=road.replace("[S2]", "[S9]")))
assert sev(F, "MEDIUM", "does not exist: S9")
F = pc.check(make(road=""))
assert sev(F, "HIGH", "No task")
F = pc.check(make(road=""), "plan")
assert not sev(F, "HIGH", "No task")

# the Feature-cell tags keep the ROADMAP columns: docs_lint contract table is still one table with the six columns
ts = pc.tasks(road)
assert [t["id"] for t in ts] == ["T-001", "T-002", "T-003", "T-004", "T-005", "T-006"]
assert ts[1]["deps"] == ["T-001"] and ts[4]["par"] and ts[0]["risk"] == [1] and ts[5]["story"] == [2]

# findings are sorted by severity and capped at 50
F = pc.check(make(const=rd(T, "CONSTITUTION.md"), plan=rd(T, "PLAN.md"), road=""))
assert [x[0] for x in F] == sorted([x[0] for x in F], key=pc.ORDER.index) and len(F) <= 50

# command line: exit code and the line that sums up
d = make()
p = subprocess.run([sys.executable, os.path.join(H, "plan_check.py"), os.path.dirname(os.path.dirname(d))], capture_output=True, text=True)
assert p.returncode == 0 and "OK, nothing blocks" in p.stdout, p.stdout
d2 = make(road="")
p = subprocess.run([sys.executable, os.path.join(H, "plan_check.py"), os.path.dirname(os.path.dirname(d2))], capture_output=True, text=True)
assert p.returncode == 1 and "to fix before building" in p.stdout

# the commands exist and name their file and checker
for name, words in (("piano", ("CONSTITUTION.md", "PLAN.md", "spec_check.py", "plan_check.py")), ("compiti", ("ROADMAP.md", "intent-gate", "[P]", "plan_check.py")),
                    ("coerenza", ("plan_check.py", "read only", "CRITICAL")), ("ambiente", ("env_check.py", "Lore", "PLAYTEST.md", "Self-healing"))):
    c = rd(ROOT, "user-level-commands", name + ".md")
    assert c.startswith("---") and "description:" in c, name
    for w in words:
        assert w.lower() in c.lower(), (name, w)
assert "Sources consulted" in rd(ROOT, "user-level-commands", "piano.md") and "skills_lib.py patterns" in rd(ROOT, "user-level-commands", "piano.md")
print("ok")
