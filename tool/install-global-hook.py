import json, os, sys
settings, script = sys.argv[1], sys.argv[2]
cmd = ("powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \"& { if (Get-Command py -ErrorAction SilentlyContinue) "
       "{ py -3 '%s' } else { python '%s' } }\"" % (script, script))
d = {}
if os.path.isfile(settings):
    d = json.load(open(settings, encoding="utf-8"))
changed = False
ss = d.setdefault("hooks", {}).setdefault("SessionStart", [])
if any("kit-sync-global" in h.get("command", "") for e in ss for h in e.get("hooks", [])):
    print("  global update hook already present")
else:
    ss.append({"matcher": "startup", "hooks": [{"type": "command", "command": cmd, "timeout": 30}]})
    changed = True
    print("  global update hook added to settings.json")
# v1.109.1: Fab lab. A Fab product has no kit files, so the MCP ledger is recorded from the profile (fab_lab.py hook).
lab = os.path.join(os.path.dirname(script), "fab_lab.py")
lab_cmd = ("powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \"& { if (Get-Command py -ErrorAction SilentlyContinue) "
           "{ py -3 '%s' hook } else { python '%s' hook } }\"" % (lab, lab))
for ev in ("PostToolUse", "PostToolUseFailure"):
    lst = d["hooks"].setdefault(ev, [])
    if any("fab_lab" in h.get("command", "") for e in lst for h in e.get("hooks", [])):
        print("  Fab lab hook (%s) already present" % ev)
        continue
    lst.append({"matcher": "mcp__unreal-mcp__call_tool", "hooks": [{"type": "command", "command": lab_cmd, "timeout": 10}]})
    changed = True
    print("  Fab lab hook (%s) added to settings.json" % ev)
for ev, matcher in (("PreToolUse", "Task|Agent"), ("SubagentStop", None)):
    lst = d["hooks"].setdefault(ev, [])
    if any("fab_lab" in h.get("command", "") for e in lst for h in e.get("hooks", [])):
        continue
    entry = {"hooks": [{"type": "command", "command": lab_cmd, "timeout": 10}]}
    if matcher:
        entry["matcher"] = matcher
    lst.append(entry)
    changed = True
    print("  Fab lab hook (%s) added to settings.json" % ev)
if changed:
    json.dump(d, open(settings, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
