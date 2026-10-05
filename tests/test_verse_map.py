import os, subprocess, sys, shutil, tempfile
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
S = os.path.join(root, "project-template", "Claude", "hooks", "verse_map.py")
SAMPLE = '''# Mgr.verse
# Summary: Manages rounds and rewards.
#   Second line of summary.
using { /Fortnite.com/Devices }

# --- BANNER ---
# Tracks one player's round state
round_state := class:
    var Score : int = 0
    var Saved : weak_map(player, int) = map{}

# Round manager
round_manager := class(creative_device):
    @editable Door : trigger_device = trigger_device{}
    @editable Spawners : []player_spawner_device = array{}
    RoundEnded<public> : event(int) = event(int){}

    OnBegin<override>()<suspends> : void =
        Door.TriggeredEvent.Subscribe(OnDoor)
        GetPlayspace().PlayerAddedEvent().Subscribe(OnJoin)
        Door.Enable()

    OnDoor(Agent : ?agent) : void =
        # WARNING: do not reset here
        Print("x")

    OnJoin(P : player) : void = {}
'''
SAMPLE2 = "helper := class:\n    Use(M : round_manager) : void = {}\n"
d = tempfile.mkdtemp()
def run(*a):
    r = subprocess.run([sys.executable, S, *a], capture_output=True, text=True); assert r.returncode == 0, r.stdout + r.stderr; return r.stdout
try:
    proj, out = os.path.join(d, "proj"), os.path.join(d, "map")
    os.makedirs(os.path.join(proj, "src")); os.makedirs(os.path.join(proj, "Claude"))
    open(os.path.join(proj, "src", "Mgr.verse"), "w").write(SAMPLE)
    open(os.path.join(proj, "src", "Helper.verse"), "w").write(SAMPLE2)
    open(os.path.join(proj, "Claude", "ignored.verse"), "w").write("x := class:\n")
    o = run("build", "--project", proj, "--out", out)
    assert "2 files" in o, o
    card = open(os.path.join(out, "cards", "src__Mgr.md"), encoding="utf-8").read()
    for needle in ("Manages rounds and rewards. Second line of summary.", "round_manager", "@editable (2)", "Door:trigger_device", "Spawners:[]player_spawner_device",
                   "events declared: RoundEnded", "OnDoor", "Door.TriggeredEvent -> OnDoor", "PlayerAddedEvent -> OnJoin", "Door: Enable", "round_state.Saved", "do not reset here",
                   "note: Tracks one player's round state"):
        assert needle in card, (needle, card)
    assert "used by (files): src/Helper.verse" in card
    assert "ignored" not in open(os.path.join(out, "INDEX.md")).read()
    assert "round_manager.Door" in run("symbol", "door", "--out", out)
    assert "current" in run("check", "--project", proj, "--out", out)
    # role overlay survives a rebuild
    run("role", "src/Helper.verse", "Utility for the manager", "--out", out); run("build", "--project", proj, "--out", out)
    assert "Utility for the manager" in open(os.path.join(out, "INDEX.md")).read()
    # change detection
    open(os.path.join(proj, "src", "Mgr.verse"), "a").write("\n# edit\n")
    c = run("check", "--project", proj, "--out", out)
    assert "STALE" in c and "changed src/Mgr.verse" in c, c
    # learning: whole map first, then only cards of changed files (script decides, no relevance guess)
    run("build", "--project", proj, "--out", out)
    l = run("learn", "--out", out); assert "FIRST PASS" in l and "2 of 2" in l, l
    assert "learned" in run("learned", "--out", out)
    l = run("learn", "--out", out); assert "incremental" in l and "0 of 2" in l, l
    open(os.path.join(proj, "src", "Helper.verse"), "a").write("\n# small update\n"); run("build", "--project", proj, "--out", out)
    l = run("learn", "--out", out); assert "1 of 2" in l and "cards/src__Helper.md" in l and "Mgr" not in l, l
    # kit_sync refreshes an existing project map at session start (no map -> nothing is created)
    sys.path.insert(0, os.path.join(root, "project-template", "Claude", "hooks")); os.environ["UEFN_KIT_TEMPLATE"] = os.path.join(d, "none")
    import kit_sync
    shutil.rmtree(os.path.join(proj, "Claude", "docs"), ignore_errors=True); kit_sync.run(proj)
    assert not os.path.exists(os.path.join(proj, "Claude", "docs", "map")), "must not create a map by itself"
    run("build", "--project", proj); kit_sync.run(proj)
    assert "current" in run("check", "--project", proj)
    shutil.rmtree(os.path.join(proj, "Claude", "docs"), ignore_errors=True); shutil.rmtree(os.path.join(proj, "Claude", "logs"), ignore_errors=True)
    # bootstrap: a project with more than 5 Verse files and no map gets one at session start; learning is announced when a genre is set
    p2 = os.path.join(d, "proj2"); os.makedirs(os.path.join(p2, "src")); os.makedirs(os.path.join(p2, "Claude", "docs"))
    for i in range(6):
        open(os.path.join(p2, "src", "F%d.verse" % i), "w").write("c%d := class:\n    Run() : void = {}\n" % i)
    r = kit_sync.run(p2); assert os.path.isfile(os.path.join(p2, "Claude", "docs", "map", "meta.json")), r
    assert any("Verse map created" in n for n in r["notes"]) and not any("LEARN" in n for n in r["notes"]), r["notes"]
    open(os.path.join(p2, "Claude", "docs", ".genre"), "w").write("roguelike")
    r = kit_sync.run(p2); assert any("LEARN: 6" in n and "first pass" in n for n in r["notes"]), r["notes"]
    run("learned", "--out", os.path.join(p2, "Claude", "docs", "map"))
    r = kit_sync.run(p2); assert not any("LEARN" in n for n in r["notes"]), r["notes"]
    # post-update restart: a marker left by the update session triggers a one-time confirmation, then disappears
    mk = os.path.join(p2, "Claude", "logs", ".post-update"); os.makedirs(os.path.dirname(mk), exist_ok=True); open(mk, "w").write("9.9.9")
    r = kit_sync.run(p2); assert any("post-update check done" in n and "nothing to learn" in n for n in r["notes"]), r["notes"]
    assert not os.path.exists(mk); r = kit_sync.run(p2); assert not any("post-update" in n for n in r["notes"])
    # nothing written into the project
    assert sorted(os.listdir(proj)) == ["Claude", "src"] and os.listdir(os.path.join(proj, "Claude")) == ["ignored.verse"]
    print("verse map tests OK")
finally:
    shutil.rmtree(d, ignore_errors=True)
