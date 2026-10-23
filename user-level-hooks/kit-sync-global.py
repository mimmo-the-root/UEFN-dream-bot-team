#!/usr/bin/env python3
"""Global SessionStart hook (lives in ~/.claude/hooks, registered in ~/.claude/settings.json).
Brings ANY project that already has the kit (even a very old one, with no hook of its own) up to the
version in ~/.claude/kit-template. Silent when there is nothing to do. Never fails a session."""
import json, os, sys

def new_map_context(base):
    """v1.108 (U2+U3): a UEFN project that has no kit yet. Returns the text for Claude, or None."""
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    try:
        import kit_install as ki
    except Exception:
        return None
    r = ki.find_uefn_root(base)
    if not r:
        return None
    root, content = r
    if ki.kit_installed(content):
        return None
    kind = ki.get_kind(root)
    inst = 'python "%s"' % os.path.join(here, "kit_install.py")
    if kind == "fab":
        return ("This UEFN project is registered as a FAB PRODUCT. Do NOT install the kit's project-template in it "
                "(its components are added to the customer's project later). Work on it normally.")
    return ("NEW UEFN PROJECT WITHOUT THE KIT (%s). Before anything else, in your first reply: "
            "1) ask ONE question with AskUserQuestion: 'Is this a map (island) or a Fab product?' "
            "(skip it only if the owner already said which). "
            "2) If MAP: run `%s \"%s\" --dry-run`, tell the owner in one line how many files will be copied, ask for a yes, "
            "then run it again with --apply (it never overwrites a file), then read Claude/SETUP-INSTRUCTIONS.md and run it "
            "(on Windows use `py -3` if `python` is not found). The kit's hooks start working from the next session; say so. "
            "3) If FAB PRODUCT: run `%s --kind \"%s\" fab` and install NOTHING: a Fab product is a small UEFN project whose "
            "components are added to the customer's project, so project-template must never be put in it. "
            "The answer is remembered outside the project, so the question is not asked again."
            % (root, inst, content, inst, root))

def maybe_auto_update(tpl):
    """Once every 6 hours start a detached background check of the newest GitHub release (kit_fetch.py --auto). It never
    delays or fails the session; the new kit reaches this project at the NEXT session start. Off: set UEFN_KIT_AUTOUPDATE=0
    or create ~/.claude/kit-auto-update.off."""
    import subprocess, time
    home = os.path.join(os.path.expanduser("~"), ".claude")
    if os.environ.get("UEFN_KIT_AUTOUPDATE") == "0" or os.path.exists(os.path.join(home, "kit-auto-update.off")):
        return False
    fetch = os.path.join(tpl, "Claude", "hooks", "kit_fetch.py")
    stamp = os.path.join(home, "kit-update-check.stamp")
    if not os.path.isfile(fetch):
        return False
    try:
        if os.path.exists(stamp) and time.time() - os.path.getmtime(stamp) < 6 * 3600:
            return False
        with open(stamp, "w") as f:
            f.write(str(time.time()))
    except OSError:
        return False
    kw = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL, "close_fds": True}
    if os.name == "nt":
        kw["creationflags"] = 0x00000008 | 0x08000000  # DETACHED_PROCESS | CREATE_NO_WINDOW
    else:
        kw["start_new_session"] = True
    subprocess.Popen([sys.executable, fetch, "--auto"], **kw)
    return True

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    base = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    tpl = os.path.join(os.path.expanduser("~"), ".claude", "kit-template")
    sync = os.path.join(tpl, "Claude", "hooks", "kit_sync.py")
    try:
        maybe_auto_update(tpl)
    except Exception:
        pass
    if not os.path.isfile(sync):
        return 0
    project = None
    for c in (base, os.path.join(base, "Content"), os.path.dirname(base)):
        if os.path.isdir(os.path.join(c, "Claude", "hooks")) and os.path.isfile(os.path.join(c, "CLAUDE.md")):
            project = c
            break
    if not project:
        ctx = new_map_context(base)
        if ctx:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ctx}}))
        return 0
    sys.path.insert(0, os.path.dirname(sync))
    os.environ["CLAUDE_PROJECT_DIR"] = project
    os.environ.setdefault("UEFN_KIT_TEMPLATE", tpl)
    import kit_sync
    kit_sync.HERE = os.path.dirname(sync)
    return kit_sync.main()

try:
    sys.exit(main())
except Exception:
    sys.exit(0)
