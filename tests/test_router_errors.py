"""Router v2 (T-033): error classes, retry-after, backoff, fallback chain; wiring with the setting ON and a fake 429 provider.
No network, temp dirs only."""
import os, random, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "user-level-hooks"))
home = tempfile.mkdtemp()
os.environ["DREAM_ROUTER_HOME"] = home
os.environ["DREAM_ROUTER_CLAUDE_SETTINGS"] = os.path.join(home, "claude-settings.json")
import router_errors as re_

fails = []
def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)

c = re_.classify_status
check("429 rate_limit", c(429) == "rate_limit")
check("408/409 timeout_conflict", c(408) == c(409) == "timeout_conflict")
check("5xx server", c(500) == c(503) == c(599) == "server")
check("0 network", c(0) == c(None) == "network")
check("other", c(400) == c(401) == c(404) == "other" and c("x") == "other")
check("retryable", re_.is_retryable("server") and not re_.is_retryable("other"))
p = re_.parse_retry_after
check("retry-after clamps", p("0") == 1 and p("500") == 60 and p("7") == 7 and p("2.5") == 2.5)
check("retry-after absent/garbage", p(None) is None and p("") is None and p("soon") is None)
check("retry-after http date", p("Thu, 01 Jan 2026 00:00:30 GMT", now=1767225600.0) == 30)
rng = random.Random(3)
b = [re_.backoff_seconds(a, rng) for a in range(12)]
check("backoff within 1-30", all(1 <= x <= 30 for x in b) and b[-1] >= 15)
check("backoff deterministic", re_.backoff_seconds(3, random.Random(9)) == re_.backoff_seconds(3, random.Random(9)))
check("pause 429 uses retry-after", re_.pause_for(429, "12") == 12)
check("pause 500 uses backoff", 1 <= re_.pause_for(500, "12", rng=random.Random(1)) <= 30)
check("pause 400 is zero", re_.pause_for(400) == 0)
t = [100.0]
skip = {}
re_.mark_failure(skip, "a", 429, "10", clock=lambda: t[0])
check("chain skips resting provider", re_.chain_after(["a", "b"], skip, clock=lambda: t[0]) == ["b"])
t[0] = 111.0
check("chain brings it back after the window", re_.chain_after(["a", "b"], skip, clock=lambda: t[0]) == ["a", "b"])

# --- router wiring, fake provider
import dream_router as dr
dr.DEFAULT_SETTINGS["explore"] = 0
dr.check_all = lambda: []
check("router_v2 defaults OFF and module imported", dr.DEFAULT_SETTINGS["router_v2"] is False and dr.router_errors is not None)
dr.providers = lambda: {"fake": {"base": "http://fake.invalid/v1", "key": "FAKE_KEY", "models": ["m1"], "prefer": []}}
dr.keys = lambda: {"FAKE_KEY": "k" * 12}
dr.endpoint = lambda p, k: ("http://fake.invalid/v1", k)
dr.provider_models = lambda name, p, key, limit=3, explore=False: ["m1"]
def fake429(url, key, payload=None, timeout=180):
    raise dr.ProviderError(dr.classify(429, "slow down"), 429, "slow down", 500.0)
def fake409(url, key, payload=None, timeout=180):
    raise dr.ProviderError(dr.classify(409, "conflict"), 409, "conflict")
dr._http = fake429
REQ = {"model": "x", "max_tokens": 10, "messages": [{"role": "user", "content": "hi"}]}
def run(v2, http):
    dr._write_json("routing.json", {"enabled": True, "chain": ["fake"], "router_v2": v2})
    dr.STATE["cooldown"].clear(); dr.STATE["breaker"].clear(); dr.STATE["bad"].clear(); dr.STATE["checked"] = {"fake": 1e18}
    dr._http = http
    try:
        dr.route(dict(REQ))
    except dr.ProviderError as e:
        pass
    import time
    return dr.STATE["cooldown"].get("fake", 0) - time.time(), dr.STATE["breaker"].get("fake", {})
off, _ = run(False, fake429)
check("OFF: retry-after unchanged (500 s)", 450 < off <= 500)
on, _ = run(True, fake429)
check("ON: 429 retry-after clamped to 60 s", 1 < on <= 60)
check("ON: provider skipped inside its window", not dr.available("fake"))
_, br = run(True, fake409)
check("ON: 409 treated as server trouble (breaker counts)", br.get("fails", 0) == 1)
_, br = run(False, fake409)
check("OFF: 409 behaviour unchanged (no breaker)", br.get("fails", 0) == 0)
print("FAILED: %s" % fails if fails else "all ok")
sys.exit(1 if fails else 0)
