"""After a reboot the app resumes the old session instead of starting a fresh one: the console hook must fire on resume too, or the console keeps serving whatever project held the port."""
import json, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "project-template", "Claude", "hooks"))
import kit_sync as K
tpl = json.load(open(os.path.join(HERE, "..", "project-template", ".claude", "settings.json"), encoding="utf-8"))
def matcher(d):
    return [e.get("matcher") for e in d["hooks"]["SessionStart"] for h in e["hooks"] if "session-start-reminder" in h.get("command", "")]
assert all("resume" in m for m in matcher(tpl)), matcher(tpl)
d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, ".claude"))
old = json.loads(json.dumps(tpl))
for e in old["hooks"]["SessionStart"]:
    if any("session-start-reminder" in h.get("command", "") for h in e["hooks"]): e["matcher"] = "startup"
json.dump(old, open(os.path.join(d, ".claude", "settings.json"), "w", encoding="utf-8"))
assert K.repair_settings(d), "an old project with matcher startup must be repaired"
new = json.load(open(os.path.join(d, ".claude", "settings.json"), encoding="utf-8"))
assert all("resume" in m for m in matcher(new)), matcher(new)
assert not K.repair_settings(d), "idempotent"
print("console resume matcher OK")
