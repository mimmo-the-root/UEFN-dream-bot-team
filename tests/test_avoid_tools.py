"""A recipe marked `avoid` (a known editor crasher) must never be named as something to call in a skill, agent or command.
Allowed: the files that explain the trap (the lab guard skill, the manual, the recipes themselves, the changelog, the plan and decision pages)."""
import glob, json, os, re, sys
root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m), c or sys.exit(1))
rec = json.load(open(os.path.join(root, "user-level-skills", "mcp-tool-contracts", "references", "areas", "recipes.json"), encoding="utf-8"))
avoid = [k for k, v in rec.items() if v.get("status") == "avoid"]
ok(bool(avoid), "at least one recipe is marked avoid")
ALLOWED = ("user-level-skills/uefn-mcp-lab-guard/", "user-level-skills/mcp-tool-contracts/", "docs/", "CHANGELOG.md", "tests/", "README.md", "project-template/Claude/reference/", "project-template/Claude/hooks/manual/")
files = []
for pat in ("user-level-skills/*/SKILL.md", "user-level-skills/*/references/**/*.md", "user-level-agents/*.md", "project-template/.claude/commands/*.md"):
    files += glob.glob(os.path.join(root, pat), recursive=True)
bad = []
for f in files:
    rel = os.path.relpath(f, root).replace(os.sep, "/")
    if rel.startswith(ALLOWED):
        continue
    t = open(f, encoding="utf-8", errors="replace").read()
    for k in avoid:
        full, short = k, k.split(".")[-1]  # StaticMeshTools/get_lod_count
        if short in t:
            bad.append((rel, short))
ok(not bad, "no skill, agent or command names an avoid tool (found: %s)" % bad[:5])
