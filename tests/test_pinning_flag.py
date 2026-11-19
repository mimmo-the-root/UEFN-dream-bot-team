"""T-080: the "pinning" flag in routing.json (default on). On = a package keeps its model; off = the old behaviour (nothing is pinned)."""
import os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "user-level-hooks")):
    if os.path.isfile(os.path.join(p, "dream_router.py")):
        sys.path.insert(0, p)
home = tempfile.mkdtemp()
os.environ["DREAM_ROUTER_HOME"] = home
os.environ["DREAM_ROUTER_CLAUDE_SETTINGS"] = os.path.join(home, "claude-settings.json")  # never the real profile
import dream_router as dr
dr.DEFAULT_SETTINGS["explore"] = 0
dr.check_all = lambda: []
dr.PORT = 1

assert dr.DEFAULT_SETTINGS.get("pinning") is True, "pinning must default to on"
dr.save_key("OK_KEY", "ok-key-1234567")
dr._http = lambda url, key, payload=None, timeout=180: {"data": [{"id": "m1"}], "choices": [{"message": {"content": "hi"}, "finish_reason": "stop"}], "usage": {"input_tokens": 5, "output_tokens": 1}}


def run(pinning):
    cfg = dict(dr._read_json("routing.json", {}), enabled=True, spread=True, chain=["ok"])
    if pinning is None:
        cfg.pop("pinning", None)  # key absent = default
    else:
        cfg["pinning"] = pinning
    dr._write_json("routing.json", cfg)
    dr.STATE["pinned"] = {}
    req = {"model": "x", "max_tokens": 5, "messages": [{"role": "user", "content": "hi"}], "metadata": {"package_id": "pkg-A"}}
    for _ in range(3):
        out, via, errors = dr.route(req)
        assert via, errors
    return dict(dr.STATE.get("pinned", {}))


on = run(True)
assert "pkg-A" in on, "pinning on: the package must be pinned"
default = run(None)
assert "pkg-A" in default, "flag absent: default is on"
off = run(False)
assert off == {}, "pinning off: nothing is pinned (old behaviour), got %r" % off
print("PASS pinning flag: on and default pin the package, off pins nothing")
