import json, os, sys
settings, script = sys.argv[1], sys.argv[2]
cmd = ("powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \"& { if (Get-Command py -ErrorAction SilentlyContinue) "
       "{ py -3 '%s' } else { python '%s' } }\"" % (script, script))
d = {}
if os.path.isfile(settings):
    d = json.load(open(settings, encoding="utf-8"))
ss = d.setdefault("hooks", {}).setdefault("SessionStart", [])
if any("kit-sync-global" in h.get("command", "") for e in ss for h in e.get("hooks", [])):
    print("  global update hook already present"); sys.exit(0)
ss.append({"matcher": "startup", "hooks": [{"type": "command", "command": cmd, "timeout": 30}]})
json.dump(d, open(settings, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("  global update hook added to settings.json")
