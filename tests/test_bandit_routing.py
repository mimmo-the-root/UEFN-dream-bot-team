"""Bandit routing (T-036): Thompson sampling converges to the better model; stats persist; deterministic. Temp dirs only."""
import os, random, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "user-level-hooks"))
os.environ["DREAM_ROUTER_HOME"] = tempfile.mkdtemp()
import bandit_routing as b

fails = []
def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)

def simulate(seed, rounds=400):
    rng, env, stats = random.Random(seed), random.Random(seed + 1), {}
    truth = {"good": (0.8, 1.0), "bad": (0.3, 1.0), "cheap": (0.8, 4.0)}  # (accept prob, cost)
    picks = {m: 0 for m in truth}
    for _ in range(rounds):
        m = b.pick(stats, "build", list(truth), rng)
        picks[m] += 1
        b.record(stats, "build", m, env.random() < truth[m][0], truth[m][1])
    return picks, stats

picks, stats = simulate(7)
check("converges to the better model (accepted per cost)", picks["good"] > 0.6 * 400 and picks["good"] > picks["bad"] and picks["good"] > picks["cheap"])
check("deterministic with the same seed", simulate(7)[0] == picks)
check("types are separate", b.arm(stats, "other", "good")["n"] == 0)

# a type where the other model is better learns the opposite
rng, env, st = random.Random(3), random.Random(4), {}
for _ in range(300):
    m = b.pick(st, "fix", ["a", "b"], rng)
    b.record(st, "fix", m, env.random() < (0.2 if m == "a" else 0.9), 1.0)
check("per package type: picks b for fix", b.arm(st, "fix", "b")["n"] > b.arm(st, "fix", "a")["n"])

p = os.path.join(tempfile.mkdtemp(), "sub", "bandit.json")
b.save(stats, p)
check("persisted stats round-trip", b.load(p) == stats)
check("missing/corrupt file gives empty", b.load(p + ".none") == {})
open(p, "w").write("{bad")
check("corrupt file gives empty", b.load(p) == {})
check("rank keeps all models", sorted(b.rank({}, "x", ["m1", "m2", "m3"], random.Random(1))) == ["m1", "m2", "m3"])
check("pick of nothing is None", b.pick({}, "x", []) is None)
sys.exit(1 if fails else 0)
