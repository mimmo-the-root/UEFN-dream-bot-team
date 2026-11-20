"""Shadow sampling (T-039): deterministic decisions, daily cap, never when free-only, loss % per type, and the router wiring
(setting ON, fake provider, no network). Temp dirs only."""
import os, random, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "user-level-hooks"))
home = tempfile.mkdtemp()
os.environ["DREAM_ROUTER_HOME"] = home
os.environ["DREAM_ROUTER_CLAUDE_SETTINGS"] = os.path.join(home, "claude-settings.json")
import shadow_sampling as sh

fails = []
def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)

# --- pure module
def run(seed, n=2000, **kw):
    rng, st = random.Random(seed), {}
    return sum(sh.decide(st, "build", rng=rng, day="2026-01-01", cap=10**9, **kw) for _ in range(n)), st
a, _ = run(5)
check("about 10% sampled by default", 140 <= a <= 260)
check("deterministic with the same seed", run(5)[0] == a)
check("rate 0 never samples", run(5, rate=0)[0] == 0)
st = {}
got = sum(sh.decide(st, "x", rng=random.Random(1), rate=1.0, cap=3, day="D1") for _ in range(10))
check("hard cap per day", got == 3 and sh.used_today(st, "D1") == 3)
check("a new day resets the cap", sh.decide(st, "x", rng=random.Random(1), rate=1.0, cap=3, day="D2"))
st = {}
check("never when free-only", not any(sh.decide(st, "x", free_only=True, rng=random.Random(i), rate=1.0, day="D") for i in range(50)) and not st)
# simulated losses: type A loses 30%, type B 0%
st, env = {}, random.Random(9)
for _ in range(1000):
    sh.record(st, "A", 1.0 if env.random() < 0.3 else 0.0)
    sh.record(st, "B", 0.0)
r = sh.report(st)
check("loss % per package type", 25 <= r["A"]["loss_pct"] <= 35 and r["B"]["loss_pct"] == 0.0 and r["A"]["n"] == 1000)
sh.save(st)
check("persists under DREAM_ROUTER_HOME", os.path.isfile(os.path.join(home, "shadow.json")) and sh.report(sh.load()) == r)
check("loss is clamped", sh.record({}, "z", 5)["loss"] == 1.0)

# --- router wiring with a fake provider
import dream_router as dr
dr.DEFAULT_SETTINGS["explore"] = 0
dr.check_all = lambda: []
check("setting defaults to OFF", dr.DEFAULT_SETTINGS["shadow_sampling"] is False and dr.shadow_sampling is not None)
prov = {"fake": {"base": "http://fake.invalid/v1", "key": "FAKE_KEY", "models": ["m1"], "prefer": []}}
dr.providers = lambda: prov
dr.keys = lambda: {"FAKE_KEY": "k" * 12}
dr.endpoint = lambda p, k: ("http://fake.invalid/v1", k)
dr.provider_models = lambda name, p, key, limit=3, explore=False: ["m1"]
dr._http = lambda url, key, payload=None, timeout=180: {"choices": [{"message": {"content": "hi"}, "finish_reason": "stop"}], "usage": {}}
dr.SHADOW_SYNC = True
judged = []
dr.SHADOW_JUDGE = lambda req, out: (judged.append(1), 0.5)[1]
req = lambda: {"model": "x", "max_tokens": 5, "metadata": {"package_type": "build"}, "messages": [{"role": "user", "content": "hi"}]}
def go(**cfg):
    dr._write_json("routing.json", dict({"enabled": True, "chain": ["fake"], "shadow_rate": 1.0, "shadow_daily_cap": 2}, **cfg))
    dr.STATE["cooldown"].clear(); dr.STATE["breaker"].clear(); dr.STATE["bad"].clear(); dr.STATE["checked"] = {"fake": 1e18}
    out, via, errs = dr.route(req())
    return out
sh.save({})
go()
check("OFF: no shadow judging", not judged and not sh.load())
sh.save({})
go(shadow_sampling=True)
check("ON: sampled and judged, loss recorded per type", len(judged) == 1 and sh.report(sh.load())["build"] == {"n": 1, "loss_pct": 50.0})
go(shadow_sampling=True)
go(shadow_sampling=True)
check("ON: daily cap holds in the router", len(judged) == 2)
sh.save({}); judged.clear()
dr.budget_allows_plan = lambda: False
go(shadow_sampling=True)
check("ON: free-only budget never judges", not judged and not sh.load().get("types"))
dr.budget_allows_plan = lambda: True
dr.SHADOW_JUDGE = lambda req, out: (_ for _ in ()).throw(RuntimeError("boom"))
check("a failing judge never breaks the answer", go(shadow_sampling=True)["content"])

if fails:
    sys.exit("FAILED: " + ", ".join(fails))
print("ok shadow_sampling")
