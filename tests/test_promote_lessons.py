"""Lessons you approved join the kit by themselves (publish.ps1 runs the promote tool with --community-only), and the Lessons tab can tell which ones are in the kit."""
import json, os, shutil, subprocess, sys, tempfile
d = tempfile.mkdtemp(); prof = os.path.join(d, "skills"); repo = os.path.join(d, "repo")
os.environ["UEFN_SKILLS_DIR"] = prof
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "project-template", "Claude", "hooks"))
import skills_lib as S
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
proj = os.path.join(d, "proj"); os.makedirs(os.path.join(proj, "Claude", "docs")); os.makedirs(os.path.join(proj, "Claude", "logs")); os.chdir(proj)
os.makedirs(repo)
S.init_genre("pirate-test")
S.propose("pirate-test", variant="base", condition="a round starts", action="teleport everyone from one manager", statement="Start rounds from one manager.", map_name="Secret Map Name", section="run-loop")
S.act("pirate-test", S.list_proposals("pirate-test")[0]["id"], "approve")
pid = [p for p in S.load_pack("pirate-test")["patterns"] if p.get("origin") == "local"][0]["id"]
row = lambda: [p for g in S.summary()["genres"] if g["slug"] == "pirate-test" for p in g["patterns"] if p["id"] == pid][0]
ok(row().get("in_kit") is False, "before the release the lesson is not in the kit")

env = dict(os.environ, UEFN_KIT_REPO=repo)
r = subprocess.run([sys.executable, os.path.join(ROOT, "tool", "promote-genre-skills.py"), "--profile", prof, "--apply", "--all", "--auto"], env=env, capture_output=True, text=True, timeout=120)
pk = os.path.join(repo, "user-level-skills", "genre", "pirate-test", "community", "pirate-test.json")
if r.returncode != 0 or not os.path.isfile(pk): print(r.returncode, r.stdout[-700:], r.stderr[-700:])
ok(r.returncode == 0 and os.path.isfile(pk), "the promote tool writes the community pack in the repo by itself")
ok(pid in open(pk, encoding="utf-8").read() and "Secret Map Name" not in open(pk, encoding="utf-8").read(), "the pack carries the lesson and no map name")
ok(os.path.isfile(os.path.join(repo, "user-level-skills", "genre", "pirate-test", "SKILL.md")), "a NEW skill with lessons goes in whole (SKILL.md too)")
ks = json.load(open(os.path.join(repo, "project-template", "Claude", "community", "kit-skills.json")))
ok(ks["skills"] == ["pirate-test"], "kit-skills.json lists the skills that ship with the kit")
S.init_genre("empty-new")
r2 = subprocess.run([sys.executable, os.path.join(ROOT, "tool", "promote-genre-skills.py"), "--profile", prof, "--apply", "--all", "--auto"], env=env, capture_output=True, text=True, timeout=120)
ok(not os.path.exists(os.path.join(repo, "user-level-skills", "genre", "empty-new")), "a new skill with nothing learned is not shipped")
sk = lambda: {g["slug"]: g for g in S.summary()["genres"]}
ok(sk()["pirate-test"]["kit"] == "new" and sk()["empty-new"]["kit"] == "none", "the Skills page data: pirate-test is new, the empty one has nothing to ship")

os.makedirs(os.path.join(prof, "genre", "pirate-test", "community"), exist_ok=True)
shutil.copy(pk, os.path.join(prof, "genre", "pirate-test", "community", "pirate-test.json"))   # what update-my-profile.cmd does after the release
ok(row().get("in_kit") is True, "after the release the lesson shows as in the kit")
kd = os.path.join(ROOT, "project-template", "Claude", "community")
ok(sk()["pirate-test"]["kit"] in ("new", "in"), "skill kit state is computed")
html = open(os.path.join(ROOT, "project-template", "Claude", "hooks", "agent-console-skills.html"), encoding="utf-8").read()
ok("<th>In the kit</th>" in html and "Not in the kit yet" in html, "the Lessons tab has the In the kit column and its filter")
print("OK")
