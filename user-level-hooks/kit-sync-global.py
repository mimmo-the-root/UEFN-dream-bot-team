#!/usr/bin/env python3
"""Global SessionStart hook (lives in ~/.claude/hooks, registered in ~/.claude/settings.json).
Brings ANY project that already has the kit (even a very old one, with no hook of its own) up to the
version in ~/.claude/kit-template. Silent when there is nothing to do. Never fails a session."""
import json, os, sys

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    base = data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    tpl = os.path.join(os.path.expanduser("~"), ".claude", "kit-template")
    sync = os.path.join(tpl, "Claude", "hooks", "kit_sync.py")
    if not os.path.isfile(sync):
        return 0
    project = None
    for c in (base, os.path.join(base, "Content"), os.path.dirname(base)):
        if os.path.isdir(os.path.join(c, "Claude", "hooks")) and os.path.isfile(os.path.join(c, "CLAUDE.md")):
            project = c
            break
    if not project:
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
