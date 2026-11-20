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
    dr.STATE["cooldown"].clear(); dr.STATE["breaker"].clear(); dr.STATE["bad"].clear(); dr.STATE.setdefault("v2skip", {}).clear(); dr.STATE["checked"] = {"fake": 1e18}
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

# --- T-033 part 2: backoff + chain_after wiring, trace headers, fallback with two fake providers
import time
dr.providers = lambda: {n: {"base": "http://fake.invalid/v1", "key": "FAKE_KEY", "models": ["m1"], "prefer": []} for n in ("pa", "pb")}
dr.STATE["checked"] = {"pa": 1e18, "pb": 1e18}
def reset(v2, chain):
    dr._write_json("routing.json", {"enabled": True, "chain": chain, "router_v2": v2, "spread": False, "pinning": False})
    for k in ("cooldown", "breaker", "bad", "v2skip"):
        dr.STATE.setdefault(k, {}).clear()
    dr.STATE["last_ok"] = None
OKRESP = {"choices": [{"message": {"content": "hi"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 3, "completion_tokens": 2}}
calls = []
def a429_then_ok(url, key, payload=None, timeout=180):
    calls.append(1)
    if len(calls) == 1:
        raise dr.ProviderError("limit", 429, "slow down", 7.0)
    return OKRESP
for v2 in (False, True):
    reset(v2, ["pa", "pb"]); del calls[:]; dr._http = a429_then_ok
    out, via, errs = dr.route(dict(REQ))
    check("fallback after 429 answers from the next provider (v2=%s)" % v2, via == "pb/m1" and len(calls) == 2)
check("ON: 429 provider rests per retry-after", "pa" in dr.STATE["v2skip"] and 1 < dr.STATE["v2skip"]["pa"] - time.time() <= 7)
del calls[:]; dr._http = lambda *a, **k: (calls.append(1), OKRESP)[1]
dr.STATE["v2skip"]["pa"] = time.time() + 30
out, via, errs = dr.route(dict(REQ))
check("ON: chain_after skips the resting provider", via == "pb/m1" and len(calls) == 1 and any("pa: resting" in e for e in errs))
dr.STATE["v2skip"]["pa"] = time.time() - 1; dr.STATE["last_ok"] = None; dr.STATE["cooldown"].clear()
out, via, errs = dr.route(dict(REQ))
check("ON: provider returns after its window", via == "pa/m1")
check("ON: success clears the rest record", "pa" not in dr.STATE["v2skip"])
reset(True, ["pa"]); dr._http = lambda *a, **k: (_ for _ in ()).throw(dr.ProviderError("server", 503, "down"))
try: dr.route(dict(REQ))
except dr.ProviderError: pass
d = dr.STATE["v2skip"].get("pa", 0) - time.time()
check("ON: 5xx rests the provider by backoff (1-30 s)", 0 < d <= 30)
reset(False, ["pa"])
try: dr.route(dict(REQ))
except dr.ProviderError: pass
check("OFF: no v2 rest record", not dr.STATE.get("v2skip"))
reset(True, ["pa", "pb"]); dr._http = lambda *a, **k: (_ for _ in ()).throw(dr.ProviderError("server", 500, "boom"))
try:
    dr.route(dict(REQ)); check("all providers failing raises", False)
except dr.ProviderError as e:
    check("all failing: existing error shape (all_failed, 529)", e.kind == "all_failed" and e.status == 529 and e.detail.startswith("All free providers failed or are paused: ") and "pa/m1: server" in e.detail and "pb/m1: server" in e.detail)
# trace headers
dr._write_json("routing.json", {"enabled": True, "router_v2": False}); 
check("OFF: no trace headers", dr.trace_headers("pa/m1") == {})
dr._write_json("routing.json", {"enabled": True, "router_v2": True}); dr.TRACE.attempts = 2
h = dr.trace_headers("pa/m1")
check("ON: trace headers", h == {"X-Router-Provider": "pa", "X-Router-Model": "m1", "X-Router-Attempts": "2"})
check("ON: no trace for local answers", dr.trace_headers("local-safety") == {})
check("trace carries no key", "k" * 12 not in json.dumps(h) if (json := __import__("json")) else False)
print("FAILED: %s" % fails if fails else "all ok")
sys.exit(1 if fails else 0)
