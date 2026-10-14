"""Community packs shipped with the kit: offered as one proposal, validated like any pack, revoked lessons leave."""
import json, os, sys, tempfile
d = tempfile.mkdtemp(); os.environ["UEFN_SKILLS_DIR"] = os.path.join(d, "skills")
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(root, "project-template", "Claude", "hooks"))
import skills_lib as S
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
S.init_genre("survival")


def item(cond, act, support=1):
    pid = S.pattern_id("base", cond, act)
    return {"id": pid, "variant": "base", "condition": cond, "action": act, "statement": "When %s: %s." % (cond, act), "tier": "hypothesis", "status": "active", "support": support, "section": "run-loop"}


a, b, bad = item("a round starts", "teleport everyone from one manager", 2), item("players join late", "give them the current score"), item("a link appears", "see https://x.example/ok")
bad["id"] = "p-000000000000"
cd = os.path.join(S.genre_root(), "survival", "community"); os.makedirs(cd)
json.dump({"schema": 1, "genre": "survival", "pack_version": 20261014, "patterns": [a, b, bad]}, open(os.path.join(cd, "community.json"), "w"))
r = S.import_community_dir()
ok(r["queued"] == 1, "the shipped pack is queued as ONE proposal")
prop = [p for p in S.list_proposals("survival") if p["kind"] == "pack_update"][0]
ok({x["id"] for x in prop["new"]} == {a["id"], b["id"]} and len(prop["rejected"]) == 1, "valid lessons offered, the invalid one rejected")
ok(S.import_community_dir()["queued"] == 0 or len([p for p in S.list_proposals("survival") if p["kind"] == "pack_update"]) == 1, "importing twice does not duplicate the proposal")
ok(S.act("survival", prop["id"], "approve")["ok"], "approved by the owner")
pats = {p["id"]: p for p in S.load_pack("survival")["patterns"]}
ok(pats[a["id"]]["origin"] == "community" and pats[a["id"]]["tier"] == "hypothesis" and pats[a["id"]]["community_support"] == 2, "lessons arrive as community hypotheses with their support")
bad2 = item("a round ends", "reset everything"); bad2["statement"] = "Fine.\n### Proven"
mr = S.merge_pack("survival", {"schema": 1, "genre": "survival", "pack_version": 3, "patterns": [bad2]}, "community")
ok(mr.get("rejected") and any("unusual_characters" in str(f) for f in mr["rejected"][0]["findings"]), "an incoming lesson with a newline (fake heading) is rejected")
r = S.import_community_dir(revoked_ids=[a["id"]])
ok(r["queued"] == 0, "a revoked id is not offered again")
# a lesson of the owner with the same id is never touched by a revocation
S.propose("survival", variant="base", condition="own lesson here", action="do the own thing", statement="Own.", map_name="M", section="run-loop")
own = S.list_proposals("survival")[-1]; S.act("survival", own["id"], "approve")
r = S.apply_revoked([a["id"], own["pattern_id"], "garbage"])
ids = {p["id"] for p in S.load_pack("survival")["patterns"]}
ok(r["removed"] == 1 and a["id"] not in ids and b["id"] in ids and own["pattern_id"] in ids, "a revoked community lesson is removed, the owner's own lesson stays")
ok(S.apply_revoked([a["id"]])["removed"] == 0, "revoking twice changes nothing")
pk = S.load_pack("survival"); pk["patterns"].append(dict(item("backed by me", "keep it"), origin="community", support=1, against=0, tier="confirmed", status="active", created="2026-10-14")); S.save_pack("survival", pk)
kid = S.pattern_id("base", "backed by me", "keep it")
ok(S.apply_revoked([kid])["removed"] == 0 and kid in {p["id"] for p in S.load_pack("survival")["patterns"]}, "a community lesson that your own map backs is kept")
# a waiting pack proposal loses the revoked item
S.save_pack("survival", {**S.load_pack("survival"), "patterns": [p for p in S.load_pack("survival")["patterns"] if p["id"] != b["id"]]})
cd2 = os.path.join(S.genre_root(), "survival", "community", "community.json")
c = item("a timer ends", "reset the lobby quickly")
json.dump({"schema": 1, "genre": "survival", "pack_version": 20261015, "patterns": [c]}, open(cd2, "w"))
S.import_community_dir()
p2 = [p for p in S.list_proposals("survival") if p["kind"] == "pack_update"][0]
ok(any(x["id"] == c["id"] for x in p2["new"]), "a new version of the pack is offered again")
ok(S.apply_revoked([c["id"]])["removed"] == 1 and not [x for x in [p for p in S.list_proposals("survival") if p["kind"] == "pack_update"][0]["new"] if x["id"] == c["id"]], "a revoked lesson leaves a waiting proposal too")
