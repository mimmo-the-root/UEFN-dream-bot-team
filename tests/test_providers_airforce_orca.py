"""T-118: providers airforce and orcarouter: free models only, never the paid ones. No network."""
import os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "user-level-hooks"))
os.environ["DREAM_ROUTER_HOME"] = tempfile.mkdtemp()
os.environ["DREAM_ROUTER_CLAUDE_SETTINGS"] = os.path.join(os.environ["DREAM_ROUTER_HOME"], "claude-settings.json")
import re
import dream_router as dr
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))

P = dr.PROVIDERS
ok("airforce" in P and "orcarouter" in P, "both providers exist")
ok(P["airforce"]["base"] == "https://api.airforce/v1" and P["orcarouter"]["base"] == "https://api.orcarouter.ai/v1", "base URLs")
ok(P["airforce"]["key"] == "AIRFORCE_API_KEY" and P["orcarouter"]["key"] == "ORCAROUTER_API_KEY", "key names")
ok(P["airforce"].get("only_prefer") and P["orcarouter"].get("only_prefer"), "only_prefer is on (never a paid model)")
pick = lambda n, m: any(re.search(x, m) for x in P[n]["prefer"])
ok(pick("airforce", "grok-4.1-mini:free") and not pick("airforce", "claude-sonnet-4.5"), "airforce takes :free only")
ok(pick("orcarouter", "orcarouter/free") and not pick("orcarouter", "orcarouter/auto"), "orcarouter takes orcarouter/free only")
ok(not P["airforce"].get("paid") and not P["orcarouter"].get("paid"), "not marked paid")
ch = dr.DEFAULT_SETTINGS["chain"]
ok("airforce" in ch and "orcarouter" in ch and ch.index("airforce") < ch.index("deepseek"), "both are in the default chain before the paid one")
print("ALL PASS")
