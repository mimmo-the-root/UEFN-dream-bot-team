"""Sharing a lesson with the community: switch on by default, only approved own lessons, only from a PUBLISHED map, the JSON passes the schema."""
import json, os, sys, tempfile, urllib.parse
d = tempfile.mkdtemp(); os.environ["UEFN_SKILLS_DIR"] = os.path.join(d, "skills")
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(root, "project-template", "Claude", "hooks")); sys.path.insert(0, os.path.join(root, "tool"))
import skills_lib as S
import contrib_schema as C
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))

proj = os.path.join(d, "proj"); os.makedirs(os.path.join(proj, "Claude", "docs")); os.makedirs(os.path.join(proj, "Claude", "logs"))
os.chdir(proj)
S.init_genre("survival")
r = S.propose("survival", variant="base", condition="a round starts", action="teleport everyone from one manager",
              statement="Start rounds from one manager.", map_name="Secret Map Name", section="run-loop")
ok(r["ok"], "lesson queued")
pid = S.list_proposals("survival")[0]["pattern_id"]
ok(S.act("survival", S.list_proposals("survival")[0]["id"], "approve")["ok"], "approved")

ok(S.community_state()["share"] is True, "the switch is ON by default (nothing leaves without pressing the button)")
S.set_community(False)
e = S.contribution_export("survival", pid)
ok(not e["ok"] and "switched off" in e["error"], "nothing can be exported while the switch is off")
ok(S.set_community(True)["share"] is True and S.community_state()["share"] is True, "the switch can be turned on")

e = S.contribution_export("survival", pid)
ok(not e["ok"] and e.get("published") is False, "map not published (no island code): the lesson stays local")
ok(S.island_published(proj)["published"] is False, "no island code means not published")
open(os.path.join(proj, "Claude", "docs", ".island-code"), "w").write("1234-5678-9012\n")
st = S.sync_published(proj, fetch=lambda c: False, force=True)
ok(st["published"] is False and not S.contribution_export("survival", pid)["ok"], "Epic has no public data: still local")
st = S.sync_published(proj, fetch=lambda c: None, force=True)
ok(st["marked"] == 0 and st["published"] is not True, "an unknown answer (offline) changes nothing and keeps the last known state")
cache = open(os.path.join(proj, "Claude", "logs", "island-published.json")).read()
ok("1234-5678-9012" not in cache, "the island code is never stored in the cache")
st = S.sync_published(proj, fetch=lambda c: True, force=True)
ok(st["published"] is True and st["marked"] == 1, "published: the map of this project is marked")

e = S.contribution_export("survival", pid)
ok(e["ok"], "now the lesson can be shared")
doc = e["doc"]
ok("Secret Map Name" not in json.dumps(doc) and "Secret" not in e["url"], "no map name leaves the computer")
rel = "contributions/survival/%s/ada.json" % pid
ok(C.validate(doc, "ada", rel) == [], "the exported JSON passes the contribution schema")
ok(len(e["url"]) < S.MAX_CONTRIB_URL and "new/main?filename=" in e["url"], "the GitHub URL is short enough")
ok(urllib.parse.unquote(e["url"]).count("<your-github-handle>") == 1, "the file name carries the handle placeholder")
ok(S.mark_shared("survival", pid)["ok"] and pid in S.community_state()["shared"], "mark_shared records it")

# a map that stops being published takes the lesson back to local
S.sync_published(proj, fetch=lambda c: False, force=True)
ok(not S.contribution_export("survival", pid)["ok"], "unpublished again: the lesson is local again")

S.sync_published(proj, fetch=lambda c: True, force=True)
ok(not S.contribution_export("survival", "p-000000000000")["ok"], "unknown lesson refused")
pack = S.load_pack("survival")
for p in pack["patterns"]:
    p["origin"] = "community"
S.save_pack("survival", pack)
ok(not S.contribution_export("survival", pid)["ok"], "a community lesson is not shared back")
os.chdir(root)
