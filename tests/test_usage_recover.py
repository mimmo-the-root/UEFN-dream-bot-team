"""A damaged or locked usage.json must never freeze the token counters (the Models page and the console chips)."""
import json, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "user-level-hooks")):
    if os.path.isfile(os.path.join(p, "dream_router.py")):
        sys.path.insert(0, p)
home = tempfile.mkdtemp()
os.environ["DREAM_ROUTER_HOME"] = home
os.environ["DREAM_ROUTER_CLAUDE_SETTINGS"] = os.path.join(home, "claude-settings.json")
import dream_router as dr

def total():
    return sum(m["requests"] for m in dr.recent_models())

dr.record_usage("zai", "glm", 10, 5)
assert total() == 1 and not dr.STATE.get("usage_error")

# 1) damaged usage.json: kept aside, counting restarts, the 72 hour counters keep going
with open(os.path.join(home, "usage.json"), "w", encoding="utf-8") as f:
    f.write('{"models": {"zai/glm": {"input": 1, "outp')  # cut in the middle
dr.record_usage("zai", "glm", 10, 5)
dr.record_usage("zai", "glm", 10, 5)
assert total() == 3, "72 hour counters must go on: %d" % total()
assert any(n.startswith("usage.json.bad-") for n in os.listdir(home)), "damaged file must be kept aside"
assert json.load(open(os.path.join(home, "usage.json"), encoding="utf-8"))["models"]["zai/glm"]["requests"] >= 1, "a new usage.json must be counting"

# 2) locked usage.json (cannot be read, not damaged): 72 hour counters still go on and the problem is visible
real = dr._read_json
def locked(name, default, keep=False):
    if name == "usage.json":
        e = dr.StateReadError(name); e.corrupt = False; raise e
    return real(name, default, keep)
dr._read_json = locked
dr.record_usage("zai", "glm", 10, 5)
dr._read_json = real
assert total() == 4 and "locked" in (dr.STATE.get("usage_error") or "")
assert "usage_error" in dr.state_view()
print("PASS usage_recover: damaged file kept aside, locked file never freezes the 72 hour counters")
