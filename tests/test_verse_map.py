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
    # kit_sync refreshes an existing project map at session start (no map -> nothing is created)
    sys.path.insert(0, os.path.join(root, "project-template", "Claude", "hooks")); os.environ["UEFN_KIT_TEMPLATE"] = os.path.join(d, "none")
    import kit_sync
    shutil.rmtree(os.path.join(proj, "Claude", "docs"), ignore_errors=True); kit_sync.run(proj)
    assert not os.path.exists(os.path.join(proj, "Claude", "docs", "map")), "must not create a map by itself"
    run("build", "--project", proj); kit_sync.run(proj)
    assert "current" in run("check", "--project", proj)
    shutil.rmtree(os.path.join(proj, "Claude", "docs"), ignore_errors=True); shutil.rmtree(os.path.join(proj, "Claude", "logs"), ignore_errors=True)
    # nothing written into the project
    assert sorted(os.listdir(proj)) == ["Claude", "src"] and os.listdir(os.path.join(proj, "Claude")) == ["ignored.verse"]
    print("verse map tests OK")
finally:
    shutil.rmtree(d, ignore_errors=True)
