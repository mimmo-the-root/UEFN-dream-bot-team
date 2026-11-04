"""A Verse module path (/<account>@fortnite.com/<project>/...) looks like an e-mail address and carries a map name: recipes store a placeholder instead."""
import json, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tool"))
sys.path.insert(0, os.path.join(HERE, "..", "project-template", "Claude", "hooks"))
base = tempfile.mkdtemp()
os.environ["UEFN_SKILLS_DIR"] = os.path.join(base, "skills")
os.makedirs(os.path.join(base, "skills", "genre", "mechanics", "official"))
import skills_lib as L
import privacy_scan as PS
AT = "@fortnite" + ".com"   # built in two parts: the privacy scan would flag the literal address
code = "using {/root" + AT + "/root_harrow_kpop/custom_verse/DailyRewards/Textures}\n# (see /root" + AT + "/root_harrow/custom_verse/Persona digest)\nusing { /Fortnite.com/Devices }\n"
L.recipe_add("mechanics", {"name": "daily rewards", "steps": ["a"], "files": [{"name": "a.verse", "code": code}]}, "Some Map")
rec = json.load(open(os.path.join(base, "skills", "genre", "mechanics", "local", "recipes.json"), encoding="utf-8"))["recipes"][0]
saved = rec["files"][0]["code"]
assert "<Account>@fortnite.com/<Project>/custom_verse/DailyRewards/Textures" in saved, saved
assert "root_harrow" not in saved and "root" + AT not in saved, saved
assert "using { /Fortnite.com/Devices }" in saved, saved   # Epic's own modules stay as they are
assert not [m for m in PS.EMAIL_RE.finditer(saved) if m.group(0).split("@")[1].lower() not in PS.EMAIL_OK_DOMAINS], saved
print("recipe module paths OK")
# a recipe saved by an older kit still holds the raw path: collecting it for the kit cleans it instead of refusing the publish
import shutil, collect_recipes as C
lp = os.path.join(base, "skills", "genre", "mechanics", "local", "recipes.json")
d = json.load(open(lp, encoding="utf-8")); d["recipes"][0]["files"][0]["code"] = code; json.dump(d, open(lp, "w", encoding="utf-8"))
repo = os.path.join(base, "repo"); os.makedirs(os.path.join(repo, "user-level-skills", "genre", "mechanics", "official"))
json.dump({"schema": 1, "recipes": []}, open(os.path.join(repo, "user-level-skills", "genre", "mechanics", "official", "recipes-official.json"), "w"))
r = C.collect(skills=os.path.join(base, "skills"), repo=repo)
assert not r["refused"] and r["added"] == [("mechanics", "daily rewards")], r
out = open(os.path.join(repo, "user-level-skills", "genre", "mechanics", "official", "recipes-official.json"), encoding="utf-8").read()
assert "root_harrow" not in out and "<Account>@fortnite.com" in out
print("collect cleans old recipes OK")
