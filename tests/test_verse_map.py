import json, os, subprocess, sys, shutil, tempfile
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
os.environ["UEFN_SKILLS_DIR"] = os.path.join(d, "skills")  # kit_sync touches the genre skills: never the real profile
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
    # learning: complete sources in batches with a receipt token; a cut-off read cannot be marked; then only changed files
    run("build", "--project", proj, "--out", out)
    l = run("learn", "--cap", "1", "--project", proj, "--out", out)
    assert "FIRST PASS" in l and "2 of 2" in l and "this batch: 1 file" in l and "--- source ---" in l and "--- end of src/" in l and "role:" in l, l
    tok = l.split("Receipt token: ")[1][:6]
    bad = subprocess.run([sys.executable, S, "learned", "zzzzzz", "--out", out], capture_output=True, text=True)
    assert bad.returncode == 1 and "REFUSED" in bad.stdout, bad.stdout
    assert "1 file(s) marked, 1 of 2" in run("learned", tok, "--out", out)
    l = run("learn", "--cap", "1", "--project", proj, "--out", out); assert "1 of 2" in l, l
    run("learned", l.split("Receipt token: ")[1][:6], "--out", out)
    l = run("learn", "--project", proj, "--out", out); assert "incremental" in l and "0 of 2" in l, l
    open(os.path.join(proj, "src", "Helper.verse"), "a").write("\n# small update\n"); run("build", "--project", proj, "--out", out)
    l = run("learn", "--project", proj, "--out", out); assert "1 of 2" in l and "=== src/Helper.verse" in l and "=== src/Mgr" not in l and "# small update" in l, l
    os.remove(os.path.join(out, "learned.json"))
    b = run("learn", "--cards-only", "--project", proj, "--out", out); f = run("learn", "--full", "--project", proj, "--out", out)
    assert "Pitfall comments" in b and "--- source ---" not in b and "cards only" in b and "functions (" in f and "--- source ---" in f, (b, f)
    # a pass that only saw cards does not count as having read the sources
    run("learned", "--all", "--out", out)
    assert "FIRST" not in run("learn", "--project", proj, "--out", out)
    st = json.load(open(os.path.join(out, "learned.json"))); st["depth"] = "cards"; json.dump(st, open(os.path.join(out, "learned.json"), "w"))
    assert "2 of 2" in run("learn", "--project", proj, "--out", out) and "0 of 2" in run("learn", "--cards-only", "--project", proj, "--out", out)
    run("learned", "--all", "--out", out)
    # documentation pass: complete documents, drift against the code map, trackers skipped, incremental by hash
    dd = os.path.join(proj, "Claude", "docs"); os.makedirs(dd, exist_ok=True)
    open(os.path.join(dd, "SPEC.md"), "w", encoding="utf-8").write("# Spec\nThe `round_manager` in Mgr.verse ends a run. `ghost_device` handles revives. See Missing.verse.\n" + "filler line\n" * 50)
    open(os.path.join(dd, "STATUS.md"), "w", encoding="utf-8").write("tracker, must be skipped\n")
    dc = run("docs", "--project", proj, "--out", out)
    assert "FIRST PASS" in dc and "1 to read" in dc and "=== Claude/docs/SPEC.md" in dc and "STATUS" not in dc, dc
    assert "ghost_device" in dc and "Missing.verse" in dc and "round_manager" not in dc.split("possible drift")[1], dc
    assert "filler line" in dc and dc.count("filler line") == 50
    dtok = dc.split("Receipt token: ")[1][:6]
    badd = subprocess.run([sys.executable, S, "docsdone", "nope00", "--project", proj, "--out", out], capture_output=True, text=True)
    assert badd.returncode == 1 and "REFUSED" in badd.stdout, badd.stdout
    nod = subprocess.run([sys.executable, S, "docsdone", dtok, "--project", proj, "--out", out], capture_output=True, text=True)
    assert nod.returncode == 1 and "no decision recorded" in nod.stdout and "Claude/docs/SPEC.md" in nod.stdout, nod.stdout  # a document cannot be skipped
    assert "status words to verify" in dc
    json.dump({"reviewed": [{"file": "Claude/docs/SPEC.md", "note": "compared with code, accurate"}]}, open(os.path.join(out, "doc-patches.json"), "w"))
    assert "1 document(s) marked" in run("docsdone", dtok, "--project", proj, "--out", out)
    assert "0 to read" in run("docs", "--project", proj, "--out", out)
    open(os.path.join(dd, "SPEC.md"), "a", encoding="utf-8").write("changed\n")
    dc2 = run("docs", "--project", proj, "--out", out); assert "incremental, 1 to read" in dc2
    assert subprocess.run([sys.executable, S, "docsdone", dc2.split("Receipt token: ")[1][:6], "--project", proj, "--out", out], capture_output=True, text=True).returncode == 1  # review was for the old version
    json.dump({"reviewed": [{"file": "Claude/docs/SPEC.md", "note": "re-checked"}]}, open(os.path.join(out, "doc-patches.json"), "w"))
    run("docsdone", dc2.split("Receipt token: ")[1][:6], "--project", proj, "--out", out)
    # reverse-engineered corrections: checked (unique anchor), applied only on request, with a backup
    spec = os.path.join(dd, "SPEC.md"); open(spec, "w", encoding="utf-8").write("# Spec\nGameManager has 3558 lines.\nSee rebirth_manager.verse.\n")
    json.dump({"patches": [{"id": "d1", "file": "Claude/docs/SPEC.md", "find": "3558 lines", "replace": "2230 lines", "reason": "split", "source": "Mgr.verse"},
                           {"id": "d2", "file": "Claude/docs/SPEC.md", "find": "nope not there", "replace": "x", "reason": "bad", "source": "-"},
                           {"id": "d3", "file": "src/Mgr.verse", "find": "round", "replace": "x", "reason": "code is not a document", "source": "-"}]}, open(os.path.join(out, "doc-patches.json"), "w"))
    lst = run("docpatch", "list", "--project", proj, "--out", out)
    assert "[pending] d1" in lst and "[invalid: find text occurs 0 times" in lst and "not a project document" in lst and "1 ready to apply" in lst, lst
    assert "3558" in open(spec).read(), "list must not change anything"
    ap = run("docpatch", "apply", "--all", "--project", proj, "--out", out)
    assert "applied d1" in ap and "skipped d2" in ap and "skipped d3" in ap, ap
    assert "2230 lines" in open(spec).read() and "round" in open(os.path.join(proj, "src", "Mgr.verse")).read()
    bk = os.path.join(proj, "Claude", "logs", "doc-backup"); assert os.path.isdir(bk) and any("3558" in open(os.path.join(r, f)).read() for r, _, fs in os.walk(bk) for f in fs)
    assert "[applied] d1" in run("docpatch", "list", "--project", proj, "--out", out) and "0 patch(es) applied" in run("docpatch", "apply", "--all", "--project", proj, "--out", out)
    run("docsdone", "--all", "--project", proj, "--out", out)
    # progress ledger + revert
    run("learned", "--all", "--out", out); os.remove(os.path.join(out, "learned.json"))
    l1 = run("learn", "--cap", "1", "--project", proj, "--out", out); assert "this batch: 1 file" in l1, l1
    stt = run("status", "--project", proj, "--out", out)
    assert "code: 0 of 2 Verse files learned" in stt and "devices: never read" in stt and "document corrections:" in stt, stt
    assert "Learning progress" in open(os.path.join(out, "PROGRESS.md")).read()
    open(os.path.join(out, "DEVICES.md"), "w").write("WIRING-READ: yes\nSETTINGS-READ: no\n")
    assert "wiring read: yes; settings read: NO" in run("status", "--project", proj, "--out", out)
    stamp = [x for x in os.listdir(os.path.join(proj, "Claude", "logs", "doc-backup"))][0]
    assert "restored from backup" in run("docpatch", "revert", stamp, "--project", proj, "--out", out) and "3558" in open(spec).read()
    run("learned", "--all", "--out", out)
    # Windows pipes use cp1252: a document with an arrow must not crash the docs pass
    open(os.path.join(dd, "SPEC.md"), "w", encoding="utf-8").write("# Spec\nrun -> win \u2192 reward \u2014 end\n")
    r = subprocess.run([sys.executable, S, "docs", "--project", proj, "--out", out], capture_output=True, env=dict(os.environ, PYTHONIOENCODING="cp1252"))
    assert r.returncode == 0 and "\u2192".encode("utf-8") in r.stdout, r.stderr
    run("docsdone", "--all", "--project", proj, "--out", out)
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
    r = kit_sync.run(p2); assert any("LEARN" in n and "6 Verse file" in n and "first pass" in n for n in r["notes"]), r["notes"]
    run("learned", "--all", "--out", os.path.join(p2, "Claude", "docs", "map"))
    r = kit_sync.run(p2); assert not any("LEARN" in n for n in r["notes"]), r["notes"]
    # a device-only map (no Verse files at all) still learns from its documents and its devices
    p3 = os.path.join(d, "proj3"); os.makedirs(os.path.join(p3, "Claude", "docs"))
    open(os.path.join(p3, "Claude", "docs", ".genre"), "w").write("sports-racing")
    open(os.path.join(p3, "Claude", "docs", "SPEC.md"), "w").write("# Spec\nA race.\n")
    r = kit_sync.run(p3); assert any("LEARN" in n and "NO Verse code" in n and "1 project document" in n for n in r["notes"]), r["notes"]
    assert "no Verse files" in open(os.path.join(p3, "Claude", "docs", "map", "PROGRESS.md")).read()
    open(os.path.join(p3, "Claude", "docs", "map", "DEVICES.md"), "w").write("WIRING-READ: yes\nSETTINGS-READ: yes\nISLAND-CONFIG-READ: yes\n")
    json.dump({"reviewed": [{"file": "Claude/docs/SPEC.md", "note": "ok"}]}, open(os.path.join(p3, "Claude", "docs", "map", "doc-patches.json"), "w"))
    run("docs", "--project", p3, "--out", os.path.join(p3, "Claude", "docs", "map")); run("docsdone", "--all", "--project", p3, "--out", os.path.join(p3, "Claude", "docs", "map"))
    r = kit_sync.run(p3); assert not any("LEARN" in n for n in r["notes"]), r["notes"]
    # post-update restart: a marker left by the update session triggers a one-time confirmation, then disappears
    mk = os.path.join(p2, "Claude", "logs", ".post-update"); os.makedirs(os.path.dirname(mk), exist_ok=True); open(mk, "w").write("9.9.9")
    r = kit_sync.run(p2); assert any("post-update check done" in n and "nothing to learn" in n for n in r["notes"]), r["notes"]
    assert not os.path.exists(mk); r = kit_sync.run(p2); assert not any("post-update" in n for n in r["notes"])
    # the hook output must be ONE JSON object even when helpers print (a map exists): otherwise Claude Code drops the message
    os.remove(os.path.join(p2, "Claude", "docs", "map", "learned.json"))
    env = dict(os.environ, CLAUDE_PROJECT_DIR=p2, UEFN_KIT_TEMPLATE=os.path.join(d, "none"))
    hook = subprocess.run([sys.executable, os.path.join(root, "project-template", "Claude", "hooks", "kit_sync.py")], capture_output=True, text=True, env=env)
    import json as _json
    out_json = _json.loads(hook.stdout); msg = out_json["systemMessage"]; assert "LEARN" in msg, hook.stdout
    assert os.path.isfile(os.path.join(p2, "Claude", "logs", "kit-sync.log")) and "emitted=True" in open(os.path.join(p2, "Claude", "logs", "kit-sync.log")).read()
    mk2 = os.path.join(p2, "Claude", "logs", ".post-update"); os.makedirs(os.path.dirname(mk2), exist_ok=True); open(mk2, "w").write("9.9.9")
    hook = subprocess.run([sys.executable, os.path.join(root, "project-template", "Claude", "hooks", "kit_sync.py")], capture_output=True, text=True, env=env)
    assert "ACTION (kit)" in _json.loads(hook.stdout)["hookSpecificOutput"]["additionalContext"], hook.stdout
    # nothing written into the project
    assert sorted(os.listdir(proj)) == ["Claude", "src"] and os.listdir(os.path.join(proj, "Claude")) == ["ignored.verse"]
    print("verse map tests OK")
finally:
    shutil.rmtree(d, ignore_errors=True)
