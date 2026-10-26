"""Stop hook: keeps the learning going in a long session.

The kit asks Claude to learn the map at the session start (kit_sync.py). A session that stays open for hours while you
develop never starts again, so the blueprint would stay out of date. At the end of an answer this script (no AI tokens)
checks whether the Verse code, the documents or the device map changed since the kit last learned them; if so, and not
more often than every 30 minutes, it asks Claude to continue with the learning ({"decision":"block"} = "keep going").
Silent when nothing is pending, when the genre is not confirmed yet, when the hook was itself caused by a Stop hook
(stop_hook_active), or in the headless runs of after-playtest (UEFN_KIT_NO_NUDGE). Any failure is swallowed."""
import contextlib, io, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
COOLDOWN = 30 * 60   # seconds between two nudges
MAX_SAME = 2         # nudges for the very same state of the project (if Claude could not finish it, do not insist)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    if payload.get("stop_hook_active") or os.environ.get("UEFN_KIT_NO_NUDGE"):
        return
    project = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.path.dirname(os.path.dirname(HERE))
    mdir = os.path.join(project, "Claude", "docs", "map")
    try:   # the owner pressed Learn on the console (Skills page): learn now, once, whatever the cooldown says
        import skills_lib as _sk
        fl = _sk.map_learn_flag(project)
        if fl and fl.get("state") == "waiting":
            fl["state"] = "sent"
            fl["sent_at"] = time.strftime("%Y-%m-%d %H:%M")
            with open(_sk._learn_flag_path(project), "w", encoding="utf-8") as f:
                json.dump(fl, f)
            print(json.dumps({"decision": "block", "reason":
                "The owner pressed LEARN on the console for this map. Do it now, without asking, then say in ONE line what you learned: "
                "follow `.claude/commands/learn-map.md` completely (code, documents, devices, the map blueprint). Then queue up to 5 general lessons about HOW things are done in this map "
                "(the steps and settings that worked for a mechanic, device, widget or Verse feature, and in which order; mistakes only as a short 'avoid' note) with "
                "`python Claude/hooks/skills_lib.py propose <genre> --variant <type> ...` after checking `skills_lib.py patterns <genre>`. "
                "The recipes of the mechanics and devices of this map were already prepared by the kit from its Verse code: complete one only if the owner confirms a step is wrong. "
                "The owner approves everything on the Skills page."}))
            return
    except Exception:
        pass
    gp = os.path.join(project, "Claude", "docs", ".genre")
    genre = open(gp, encoding="utf-8").read().strip() if os.path.isfile(gp) else ""
    if not genre or genre == "epic-template":
        return
    import verse_map
    try:
        import skills_lib
        if skills_lib.genre_gate(project):
            return  # genre/type not confirmed by the owner yet: nothing to learn into
    except Exception:
        pass
    sp = os.path.join(project, "Claude", "logs", "learn-nudge.json")
    try:
        st = json.load(open(sp, encoding="utf-8"))
    except Exception:
        st = {}
    if time.time() - st.get("at", 0) < COOLDOWN:
        return
    has_map = os.path.isfile(os.path.join(mdir, "meta.json"))
    if has_map:
        with contextlib.redirect_stdout(io.StringIO()):
            verse_map.cmd_build(project, mdir)   # picks up Verse files changed since the map was built (script, no tokens)
    lr = verse_map.learn_pending(mdir)
    no_code = lr is None
    if not has_map and not no_code:
        return
    pend = len(lr[1]) if lr else 0
    dp = verse_map.docs_pending(project, mdir) if (lr or no_code) else (True, [])
    pend_docs = len(dp[1])
    prof = verse_map.profile_pending(mdir, project)
    if not (pend or pend_docs or prof):
        return
    fp = verse_map.profile_fingerprint(project, mdir)
    same = st.get("n", 0) if st.get("fp") == fp else 0
    if same >= MAX_SAME:
        return
    os.makedirs(os.path.dirname(sp), exist_ok=True)
    with open(sp, "w", encoding="utf-8") as f:
        json.dump({"fp": fp, "at": time.time(), "n": same + 1}, f)
    what = []
    if pend:
        what.append("%d Verse file(s) changed or not read" % pend)
    if pend_docs:
        what.append("%d project document(s) changed or not read" % pend_docs)
    if prof:
        what.append("the map blueprint is out of date")
    reason = ("LEARN (automatic, the owner has been developing in this long session): " + "; ".join(what) + ". "
              "Do it now without asking and without a long preamble, then go back to the owner's work: follow `.claude/commands/learn-map.md` "
              "(code with `verse_map.py learn`, documents with `verse_map.py docs`, devices only if they changed, then the map blueprint, step 8). "
              "Only what changed is read. Finish with ONE line saying what was updated.")
    print(json.dumps({"decision": "block", "reason": reason}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
