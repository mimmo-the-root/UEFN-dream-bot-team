import os, sys, json, tempfile, shutil
d = tempfile.mkdtemp(); os.environ["UEFN_SKILLS_DIR"] = d
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(root, "project-template", "Claude", "hooks"))
import skills_lib as S
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
try:
    S.init_genre("roguelike")
    refs = os.path.join(d, "genre", "roguelike", "references"); os.makedirs(refs, exist_ok=True)
    shutil.copy(os.path.join(root, "user-level-skills", "genre", "roguelike", "references", "starter-sections.json"), refs)
    ok(len(S.starter_sections("roguelike")) == 8, "8 starter sections load")
    S.init_genre("gun-game")  # a genre without its own sections file still gets the 8 default sections and a starter
    ok([x["id"] for x in S.starter_sections("gun-game")] == [x["id"] for x in S.starter_sections("roguelike")], "genre without sections file gets the 8 defaults")
    rg = S.propose("gun-game", map_name="Map G", section="death-strategies", variant="*", condition="a player is eliminated", action="respawn at once and keep the weapon tier", statement="Respawn keeps tier.")
    ok(rg["ok"] and S.act("gun-game", rg["proposal"], "approve")["ok"], "gun-game pattern with a default section approved")
    ok("respawn at once" in open(os.path.join(d, "genre", "gun-game", "references", "starter.md"), encoding="utf-8").read(), "gun-game starter.md generated")
    rw = S.propose("battle-royale", map_name="Map W", section="run-loop", variant="*", condition="a round has one winner", action="end the round when one player is left", statement="End on last player.")
    ok(rw["ok"], "lesson queued under a wrongly guessed genre")
    rt = S.retarget("battle-royale", "party-mini-games"); ok(rt["ok"] and rt["moved"] == 1, "retarget moves the waiting lesson")
    ok(not S.list_proposals("battle-royale") and len(S.list_proposals("party-mini-games")) == 1, "lesson now waits under the right genre")
    import tempfile as _tf
    pj = _tf.mkdtemp()
    pr = S.save_profile("party-mini-games", "Map P", {"concept": "Last player standing on 12 pillars around a central one", "layout": [{"element": "Pillars", "count": 12, "note": "ring + 1 central"}],
         "loop": ["lobby", "match 8 min", "end"], "devices": [{"class": "Item Granter", "count": 6, "role": "weapons every N damage"}], "rules": [{"when": "every N damage dealt", "then": "granter gives a weapon", "numbers": "N=500"}],
         "build_order": ["place pillars", "place granters"]}, project=pj)
    ok(pr["ok"] and os.path.isfile(os.path.join(pj, "Claude", "docs", "map", "profile-learned.json")), "map blueprint saved with a marker")
    sm = open(os.path.join(d, "genre", "party-mini-games", "references", "starter.md"), encoding="utf-8").read()
    ok("Map anatomy" in sm and "**Pillars** (1 of 1 map(s))" in sm and "Item Granter" in sm and "N=500" in sm and "Map P" not in sm, "starter shows the map anatomy without the map name")
    # the project keeps a copy of the blueprint: a fresh profile (new PC) gets it back
    import shutil as _sh, json as _js
    _js.dump({"concept": "x pillars", "layout": [{"element": "Pillars", "count": 12}]}, open(os.path.join(pj, "Claude", "docs", "map", "profile.json"), "w"))
    mk = _js.load(open(os.path.join(pj, "Claude", "docs", "map", "profile-learned.json")))["map_key"]
    _sh.rmtree(os.path.join(d, "genre", "party-mini-games", "local", "profiles"))
    ok(S.sync_profile_from_project(pj).startswith("map blueprint restored") and os.path.isfile(os.path.join(d, "genre", "party-mini-games", "local", "profiles", mk + ".json")), "blueprint restored into the genre skill from the project copy")
    P = dict(variant="run-based-coop", condition="two players trigger the same exit at once", action="set a lock before the first suspend and release it on every exit",
             statement="Guard shared transitions with a lock set before the first suspend.")
    ok(not S.propose("roguelike", map_name="Map One", section="Bad Section!", **P)["ok"], "bad section id rejected")
    r = S.propose("roguelike", map_name="Map One", section="architecture", **P); ok(r["ok"], "proposal with section queued")
    ok(S.act("roguelike", r["proposal"], "approve")["ok"], "approved")
    st = open(os.path.join(refs, "starter.md"), encoding="utf-8").read()
    arch = st.split("## 2. Architecture")[1].split("## 3.")[0]
    ok("lock before the first suspend" in arch.replace("set a lock before the first suspend", "lock before the first suspend") and "hypothesis" in arch, "pattern appears under its section with its tier")
    ok("Not classified yet" not in st, "no unclassified patterns")
    # a pattern approved without a section shows up as unclassified, then set_section moves it
    P2 = dict(variant="*", condition="a player leaves during a run", action="clear that player's run state at once", statement="Clear per-player run state on leave.")
    r2 = S.propose("roguelike", map_name="Map One", **P2); S.act("roguelike", r2["proposal"], "approve")
    ok("Not classified yet" in open(os.path.join(refs, "starter.md"), encoding="utf-8").read(), "unsectioned pattern listed as not classified")
    pid2 = [p["id"] for p in S.load_pack("roguelike")["patterns"] if p["variant"] == "*"][0]
    ok(not S.set_section("roguelike", pid2, "nope")["ok"], "unknown section refused")
    ok(S.set_section("roguelike", pid2, "persistence")["ok"], "section assigned")
    st = open(os.path.join(refs, "starter.md"), encoding="utf-8").read()
    ok("Not classified yet" not in st and "clear that player" in st.split("## 6. Persistence")[1].split("## 7.")[0], "moved under Persistence")
    # a second map backing the pattern raises its tier in the starter (it evolves with new maps)
    r3 = S.propose("roguelike", map_name="Map Two", section="architecture", **P); S.act("roguelike", r3["proposal"], "approve")
    ok("confirmed" in open(os.path.join(refs, "starter.md"), encoding="utf-8").read().split("## 2. Architecture")[1].split("## 3.")[0], "tier evolves with a second map")
    # near-duplicates are listed (never merged by themselves); rendering keeps the original capitalisation
    Pd = dict(variant="run-based-coop", condition="two players trigger the same exit at the same time", action="set a lock before the first suspend and release it on every exit path",
              statement="Lock shared exits before suspending.")
    rd = S.propose("roguelike", map_name="Map One", section="architecture", **Pd); S.act("roguelike", rd["proposal"], "approve")
    sim = S.similar("roguelike"); ok(len(sim) >= 1 and sim[0]["score"] >= 0.5, "similar patterns are listed")
    P4 = dict(variant="*", condition="a UI Widget stays open after the Player left", action="close it from PlayerRemovedEvent", statement="Close widgets on leave.")
    r4 = S.propose("roguelike", map_name="Map One", section="performance", **P4); S.act("roguelike", r4["proposal"], "approve")
    ok("UI Widget stays open after the Player left" in open(os.path.join(refs, "starter.md"), encoding="utf-8").read(), "original case kept in the starter")
    ex = S.export_pack("roguelike", os.path.join(d, "out")); ok(ex["ok"], "export ok")
    ok(any(p.get("section") == "architecture" for p in json.load(open(ex["path"]))["patterns"]), "section is exported (shareable)")
    # genre confirmation: nothing is written to the genre skills until the owner confirms genre and map type
    gp = _tf.mkdtemp(); os.makedirs(os.path.join(gp, "Claude", "docs"))
    open(os.path.join(d, "genre", "fortnite-genres-official.json"), "w").write(json.dumps({"genres": [{"slug": "party-mini-games", "name": "Party & Mini Games"}, {"slug": "battle-royale", "name": "Battle Royale"}]}))
    ok(not S.propose_genre(gp, "not-a-genre", "pillars")["ok"], "an unknown genre is refused")
    ok(S.propose_genre(gp, "battle-royale", "Pillars Arena", "12 pillars")["ok"], "genre proposal written")
    ok(not os.path.isdir(os.path.join(d, "genre", "battle-royale", "local", "profiles")), "proposal does not create a profile")
    ok(S.genre_gate(gp) and "NOT CONFIRMED" in S.genre_gate(gp)["error"], "gate closed while the proposal is pending")
    ok(not S.save_profile("battle-royale", "Map Q", {"concept": "x", "layout": [{"element": "a", "count": 1}]}, gp)["ok"], "blueprint refused while pending")
    st = S.genre_state(gp); ok(st["status"] == "pending" and st["variant"] == "pillars-arena", "console state shows the pending proposal and the free type name")
    ok(S.confirm_genre(gp, "party-mini-games", "pillars")["ok"] and S.genre_gate(gp) is None, "owner correction confirms genre and type")
    ok(open(os.path.join(gp, "Claude", "docs", ".genre")).read().strip() == "party-mini-games", ".genre follows the owner's choice")
    pr2 = S.save_profile("party-mini-games", "Map Q", {"concept": "pillars", "layout": [{"element": "Pillars", "count": 12}]}, gp)
    ok(pr2["ok"] and "pillars" in S.genre_state(gp)["known_variants"]["party-mini-games"], "blueprint carries the confirmed type and it is offered for the next map")
    import verse_map as _vm
    ls = _vm.learning_status(gp, os.path.join(gp, "Claude", "docs", "map"))
    ok([x["key"] for x in ls["steps"]] == ["code", "docs", "devices", "island", "blueprint"] and ls["log"] and ls["blueprint_state"] == "current", "learning state for the console")
    md = os.path.join(gp, "Claude", "docs", "map"); open(os.path.join(md, "DEVICES.md"), "w").write("WIRING-READ: yes\nSETTINGS-READ: no\nISLAND-CONFIG-READ: yes\nISLAND-CONFIG-SUMMARY: 16 players, 3 rounds\n")
    ls = _vm.learning_status(gp, md); ls = _vm.learning_status(gp, md)
    kinds = [e["kind"] for e in ls["log"]]
    ok(kinds.count("DEVICES") == 1 and kinds.count("ISLAND") == 1, "devices and island configuration are logged by themselves, once")
    ok(S.console_learning(gp)["genre_state"]["genre"] == "party-mini-games", "console learning payload (shared by both console servers)")
    n0 = len(S._profiles("party-mini-games"))
    S.save_profile("party-mini-games", "Another Name", {"concept": "pillars v2", "layout": [{"element": "Pillars", "count": 12}]}, gp)
    ok(len(S._profiles("party-mini-games")) == n0, "same project saved under another map name does not create a second blueprint")
    S.save_profile("party-mini-games", "Map Z", {"concept": "other map", "layout": [{"element": "x", "count": 1}]})
    ok(len(S._profiles("party-mini-games")) == n0 + 1, "a different map still gets its own blueprint")
    lb = [p["label"] for p in S._profiles("party-mini-games")][0]
    ok(S.drop_profile("party-mini-games", lb)["ok"] and sorted(p["label"] for p in S._profiles("party-mini-games")) == ["Map %d" % i for i in range(1, n0 + 1)], "duplicate blueprint dropped, labels renumbered")
    # confirming on the console saves what was written while waiting: the blueprint and the lessons held back
    g2 = _tf.mkdtemp(); os.makedirs(os.path.join(g2, "Claude", "docs", "map"))
    S.propose_genre(g2, "party-mini-games", "capture-flag", "2 teams")
    json.dump({"concept": "two teams capture the flag", "layout": [{"element": "Flags", "count": 2}]}, open(os.path.join(g2, "Claude", "docs", "map", "profile.json"), "w"))
    cwd0 = os.getcwd(); os.chdir(g2)
    try:
        held = S.propose("party-mini-games", map_name="Map F", section="run-loop", variant="capture-flag", condition="a flag carrier is eliminated", action="return the flag to its base", statement="Return the flag on carrier death.")
    finally:
        os.chdir(cwd0)
    ok(not held["ok"] and held.get("held"), "a lesson is held while the genre is not confirmed")
    nb = len(S._profiles("party-mini-games")); nl = len(S.list_proposals("party-mini-games"))
    cf = S.confirm_genre(g2, "party-mini-games", "capture-flag")
    ok(cf["ok"] and cf["saved"]["blueprint"] and cf["saved"]["lessons"] == 1, "confirmation saves the blueprint and queues the held lesson")
    ok(len(S._profiles("party-mini-games")) == nb + 1 and len(S.list_proposals("party-mini-games")) == nl + 1, "blueprint and lesson are now in the genre skill")
    # follow-ups after the blueprint: read the unknown items (2 tries), then propose general lessons once
    g3 = _tf.mkdtemp(); m3 = os.path.join(g3, "Claude", "docs", "map"); os.makedirs(m3)
    prof3 = {"concept": "race", "layout": [{"element": "Checkpoints", "count": 20}], "unknown": ["XP per accolade"]}
    json.dump(prof3, open(os.path.join(m3, "profile.json"), "w"))
    S.save_profile("sports-racing", "Map R", prof3, g3)
    ok(_vm.profile_followup(m3) == "gaps", "blueprint with unknown items asks to read them")
    _vm.marker_update(m3, gap_tries=2)
    ok(_vm.profile_followup(m3) == "lessons", "after two tries the general lessons are asked")
    _vm.marker_update(m3, lessons_asked=1)
    ok(_vm.profile_followup(m3) == "", "each follow-up is asked only once")
    S.save_profile("sports-racing", "Map R", dict(prof3, unknown=[]), g3)
    st3 = _vm._read_state(os.path.join(m3, "profile-learned.json")); ok(st3["lessons_asked"] == 1 and st3["unknown_n"] == 0, "saving again keeps the follow-up counters")
    print("starter tests OK")
finally:
    shutil.rmtree(d, ignore_errors=True)
