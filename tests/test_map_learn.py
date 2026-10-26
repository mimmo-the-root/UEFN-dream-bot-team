"""Learn button of a map project: flag, no-AI recipes, Stop hook asks the agent once; projects list for the Skills page."""
import json, os, shutil, subprocess, sys, tempfile
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
HOOKS = os.path.join(ROOT, "project-template", "Claude", "hooks")
sys.path.insert(0, HOOKS)
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
base = tempfile.mkdtemp()
try:
    os.environ["UEFN_SKILLS_DIR"] = os.path.join(base, "skills")
    import skills_lib as sl
    proj = os.path.join(base, "MyIsland", "Content")
    os.makedirs(os.path.join(proj, "Claude", "docs"))
    ok(sl.project_name(proj) == "MyIsland" and sl.project_name(os.path.join(base, "Other")) == "Other", "a project inside .../Content is named after the folder above it")
    ok(sl.map_learn_flag(proj) is None, "no request at the start")
    r = sl.map_learn_request(proj)
    ok(sl.map_learn_flag(proj)["state"] == "waiting" and "recipes" in r, "the button leaves a request for the agent")
    sl.init_genre("mechanics")
    sl.recipe_add("mechanics", {"name": "Door opener", "use": "opens a door", "steps": ["place it", "wire it"], "kind": "device"}, "MyIsland")
    ok([x["name"] for x in sl.recipes_of("MyIsland")] == ["door opener"], "the recipes of a project are listed by its name")
    sl.init_genre("platformer")
    sl.propose("platformer", "*", "a round starts", "reset the scores", "Reset the scores when a round starts", "MyIsland")
    home = os.path.join(base, "home")
    os.makedirs(os.path.join(home, ".claude"))
    json.dump({os.path.join(base, "MyIsland"): {"kind": "map", "name": "MyIsland"}}, open(os.path.join(home, ".claude", "kit-projects.json"), "w"))
    old_home = os.environ.get("USERPROFILE"), os.environ.get("HOME")
    os.environ["HOME"] = os.environ["USERPROFILE"] = home
    rows = sl.summary()["projects"]
    os.environ["HOME"], os.environ["USERPROFILE"] = old_home[1] or "", old_home[0] or ""
    mine = [x for x in rows if x["name"] == "MyIsland"]
    ok(len(mine) == 1 and mine[0]["kind"] == "map" and mine[0]["recipes"] == 1, "a registered map is listed with its recipes")
    env = dict(os.environ, CLAUDE_PROJECT_DIR=proj, UEFN_KIT_NO_NUDGE="")
    out = subprocess.run([sys.executable, os.path.join(HOOKS, "learn_nudge.py")], input="{}", capture_output=True, text=True, env=env).stdout
    ok('"block"' in out and "LEARN on the console" in out, "the Stop hook asks the agent to learn, whatever the cooldown")
    ok(sl.map_learn_flag(proj)["state"] == "sent", "the request is marked as sent")
    out2 = subprocess.run([sys.executable, os.path.join(HOOKS, "learn_nudge.py")], input="{}", capture_output=True, text=True, env=env).stdout
    ok("LEARN on the console" not in out2, "it asks once, never in a loop")
finally:
    shutil.rmtree(base, ignore_errors=True)
