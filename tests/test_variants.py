"""Map types written two ways (pillar / pillars) are one type: new lessons take the existing spelling, old data is merged."""
import os, sys, json, tempfile
d = tempfile.mkdtemp(); os.environ["UEFN_SKILLS_DIR"] = d
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(root, "project-template", "Claude", "hooks"))
import skills_lib as S
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
ok(S._variant_stem("pillar") == S._variant_stem("pillars") == S._variant_stem("Pillars".lower()), "pillar/pillars share a stem")
ok(S._variant_stem("red-vs-blue") != S._variant_stem("red-blue"), "different types stay different")
S.init_genre("party-mini-games")
P = dict(condition="a round starts", action="teleport everyone to the pillars", statement="Start rounds from one manager.", stance="for")
r = S.propose("party-mini-games", variant="pillars", map_name="Map A", section="run-loop", **P); ok(r["ok"], "lesson queued as pillars")
ok(S.act("party-mini-games", r["proposal"], "approve")["ok"], "approved")
r2 = S.propose("party-mini-games", variant="pillar", map_name="Map B", section="run-loop", **dict(P, condition="players wait", action="keep waits under 30 seconds", statement="Short waits."))
ok(r2["ok"] and S.list_proposals("party-mini-games")[0]["variant"] == "pillars", "'pillar' takes the existing spelling 'pillars'")
# legacy data: the same lesson under both spellings, a blueprint and a waiting proposal on the short one
pack = S.load_pack("party-mini-games")
base = dict(pack["patterns"][0])
legacy = dict(base, variant="pillar", id=S.pattern_id("pillar", base["condition"], base["action"]))
other = {"id": S.pattern_id("pillar", "a pillar falls", "one event feeds score"), "variant": "pillar", "statement": "One event, two consumers.", "condition": "a pillar falls",
         "action": "one event feeds score", "tier": "hypothesis", "status": "active", "origin": "local", "support": 1, "against": 0, "section": "run-loop"}
pack["patterns"] += [legacy, other]; S.save_pack("party-mini-games", pack)
sup = S._support("party-mini-games"); sup[legacy["id"]] = {"for": ["mapb"], "against": []}; sup[other["id"]] = {"for": ["mapb"], "against": []}; S._save_support("party-mini-games", sup)
S.save_profile("party-mini-games", "Map B", {"concept": "x", "layout": [{"element": "a", "count": 1}], "variant": "pillar"})
res = S.merge_variants("party-mini-games")
ok(res["ok"] and res["merged"], "merge reports what it changed")
pats = S.load_pack("party-mini-games")["patterns"]
canon = {p["variant"] for p in pats}
ok(len(canon) == 1 and canon <= {"pillar", "pillars"}, "one spelling left in the pack")
canon = canon.pop()
ok(len(pats) == 2 and all(p["id"] == S.pattern_id(p["variant"], p["condition"], p["action"]) for p in pats), "duplicate lesson merged, ids consistent")
a = [p for p in pats if p["condition"] == "a round starts"][0]
ok(a["support"] == 2 and a["tier"] == "confirmed", "support of both spellings added up (2 maps = confirmed)")
ok(S._known_variants()["party-mini-games"] == [canon], "the console lists one type")
ok(all(p.get("variant") in (None, canon) for p in S._profiles("party-mini-games")), "blueprint follows")
ok(S.merge_variants("party-mini-games")["merged"] == [], "second run changes nothing")
# the type confirmed for the project wins when it is given
pj = tempfile.mkdtemp(); os.makedirs(os.path.join(pj, "Claude", "docs"))
S.init_genre("gun-game")
for i in range(2):
    r = S.propose("gun-game", variant="duel", map_name="Map D%d" % i, section="run-loop", condition="cond %d" % i, action="act %d" % i, statement="Statement %d." % i)
    S.act("gun-game", r["proposal"], "approve")
pk = S.load_pack("gun-game")
pk["patterns"].append({"id": S.pattern_id("duels", "cond x", "act x"), "variant": "duels", "statement": "Legacy.", "condition": "cond x", "action": "act x",
                       "tier": "hypothesis", "status": "active", "origin": "local", "support": 1, "against": 0})
S.save_pack("gun-game", pk)
ok({p["variant"] for p in S.load_pack("gun-game")["patterns"]} == {"duel", "duels"}, "setup: two spellings, 'duel' is the most used")
S._pwrite(pj, {"genre": "gun-game", "variant": "duels", "status": "confirmed", "at": "2026-01-01"})
S.merge_variants("gun-game", pj)
ok({p["variant"] for p in S.load_pack("gun-game")["patterns"]} == {"duels"} and S._pread(pj)["variant"] == "duels", "the project's confirmed spelling wins")
