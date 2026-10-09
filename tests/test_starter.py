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
    print("starter tests OK")
finally:
    shutil.rmtree(d, ignore_errors=True)
