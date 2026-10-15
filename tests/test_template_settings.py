"""Template permissions stay safe and narrow; every kit command reaches existing projects through /kit-update."""
import os, sys, json, re
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
tpl = os.path.join(root, "project-template")
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
allow = json.load(open(os.path.join(tpl, ".claude", "settings.json"), encoding="utf-8-sig"))["permissions"]["allow"]
ok(len(allow) > 0, "safe commands are pre-approved")
bad = [r for r in allow if re.search(r"Bash\((py|python|python3)(\s+-3)?(:\*|\s\*)\)|:\*\)$|\brm\b|\bmv\b|\bpush\b|\bcommit\b|\breset\b|\bcurl\b|\bchmod\b|\bdel\b", r)]
ok(not bad, "no broad interpreter rule and nothing that writes, deletes or publishes: %s" % bad)
ok(not any(re.search(r"verse_map\.py \*", r) for r in allow) and all(re.search(r"verse_map\.py (check|symbol|build) ", r) for r in allow if "verse_map" in r), "verse_map is limited to check, symbol and build (not docpatch)")
scripts = os.listdir(os.path.join(tpl, "Claude", "hooks"))
named = [re.search(r"Claude/hooks/([\w.]+)[ )]", r).group(1) for r in allow if "Claude/hooks/" in r]
ok(all(n in scripts for n in named), "every allowed script exists in the kit")
ok(all(r.startswith("Bash(git ") and r.split()[1] in ("status", "diff", "log") for r in allow if "Claude/hooks/" not in r), "only read-only git commands")
src = open(os.path.join(tpl, "Claude", "hooks", "kit_sync.py"), encoding="utf-8").read()
managed = re.search(r"^MANAGED = \((.*?)\)$", src, re.M).group(1)
for f in os.listdir(os.path.join(tpl, ".claude", "commands")):
    ok(".claude/commands/%s" % f in managed, "command %s is delivered to existing projects" % f)
ok(all(re.search(r"mcp_map\.py --find \*\)$", r) for r in allow if "mcp_map" in r), "mcp_map is pre-approved only for --find (searching the map), never for --now")
ok(all(re.search(r"ui_kit_check\.py --(check|diff)\)$", r) for r in allow if "ui_kit_check" in r), "ui_kit_check is pre-approved only for --check and --diff (never --accept)")
