"""learn_nudge.py (Stop hook): asks to continue learning in a long session, once per change, never more often than the cooldown."""
import os, sys, json, subprocess, tempfile, time
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
hooks = os.path.join(root, "project-template", "Claude", "hooks")
script = os.path.join(hooks, "learn_nudge.py")
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
sk = tempfile.mkdtemp(); os.makedirs(os.path.join(sk, "genre"))
pj = tempfile.mkdtemp()
for d in ("Claude/docs/map", "Claude/logs", "custom_verse"):
    os.makedirs(os.path.join(pj, d))
for i in range(6):   # enough files for a Verse map
    open(os.path.join(pj, "custom_verse", "f%d.verse" % i), "w").write("using { /Fortnite.com/Devices }\nf%d := class(creative_device):\n    OnBegin<override>()<suspends>:void = {}\n" % i)
env = dict(os.environ, UEFN_SKILLS_DIR=sk, CLAUDE_PROJECT_DIR=pj)
env.pop("UEFN_KIT_NO_NUDGE", None)
def run(payload=None, e=None):
    r = subprocess.run([sys.executable, script], input=json.dumps(payload or {}), capture_output=True, text=True, env=e or env)
    return r.stdout.strip()
sys.path.insert(0, hooks)
import verse_map
ok(run() == "", "no genre: silent")
open(os.path.join(pj, "Claude", "docs", ".genre"), "w").write("party-mini-games")
verse_map.cmd_build(pj, os.path.join(pj, "Claude", "docs", "map"))
out = run()
ok(out and json.loads(out)["decision"] == "block" and "LEARN" in json.loads(out)["reason"], "pending learning: asks Claude to continue")
ok(run() == "", "cooldown: no second nudge right away")
st = os.path.join(pj, "Claude", "logs", "learn-nudge.json")
s = json.load(open(st)); s["at"] = time.time() - 3600; json.dump(s, open(st, "w"))
ok(run({"stop_hook_active": True}) == "", "a stop caused by a stop hook is never nudged again")
ok(run(e=dict(env, UEFN_KIT_NO_NUDGE="1")) == "", "headless runs are not nudged")
ok(run() != "", "after the cooldown it asks again")
s = json.load(open(st)); s["at"] = time.time() - 3600; json.dump(s, open(st, "w"))
ok(run() == "", "same state asked twice already: it does not insist")
