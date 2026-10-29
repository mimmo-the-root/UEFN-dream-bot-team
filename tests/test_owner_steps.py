import os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "project-template", "Claude", "hooks"))
import owner_steps, release_gate

with tempfile.TemporaryDirectory() as d:
    docs = os.path.join(d, "Claude", "docs"); os.makedirs(docs)
    owner_steps.add(d, "setup", "Assign RoundTimer", "Details of the manager")
    owner_steps.add(d, "gameplay", "Play one round", "Check the score")
    owner_steps.add(d, "setup", "Assign RoundTimer", "again")  # same title: not duplicated
    owner_steps.add(d, "setup", "Pick the teams")
    its = owner_steps.items(owner_steps.read(owner_steps.path_for(d)))
    assert [i["section"] for i in its] == ["setup", "setup", "gameplay"], its
    assert owner_steps.open_count(d, "setup") == 2
    assert not owner_steps.wait(d, "setup", 0.1)
    p = owner_steps.path_for(d)
    lines = open(p, encoding="utf-8").read().split("\n")
    n = next(i for i, l in enumerate(lines) if "Assign RoundTimer" in l)
    h = release_gate.line_hash(lines[n].split("] ", 1)[1])
    assert release_gate.tick(p, n + 1, True, h)["ok"]
    assert owner_steps.open_count(d, "setup") == 1
    assert not release_gate.tick(p, n + 1, True, "wrong")["ok"]
    m = next(i for i, l in enumerate(open(p, encoding="utf-8").read().split("\n")) if "Pick the teams" in l)
    release_gate.tick(p, m + 1, True, release_gate.line_hash("**Pick the teams**"))
    assert owner_steps.wait(d, "setup", 1)
print("ok test_owner_steps")
